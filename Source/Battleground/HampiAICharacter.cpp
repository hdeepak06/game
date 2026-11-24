#include "HampiAICharacter.h"

#include "HampiSoldierCharacter.h"

#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimationAsset.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/DamageType.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Sound/SoundWave.h"
#include "UObject/ConstructorHelpers.h"

AHampiAICharacter::AHampiAICharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	AIControllerClass = AAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
	bUseControllerRotationYaw = false;
	GetCharacterMovement()->bOrientRotationToMovement = false;
	GetCharacterMovement()->MaxWalkSpeed = MaxLocomotionSpeed;
	GetCapsuleComponent()->InitCapsuleSize(42.0f, 96.0f);

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> SoldierFinder(
		TEXT("/Game/Characters/Soldier/SKM_HampiSoldier.SKM_HampiSoldier"));
	if (SoldierFinder.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(SoldierFinder.Object);
		GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -96.0f));
		GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
	}

	static ConstructorHelpers::FObjectFinder<UAnimationAsset> LocomotionFinder(
		TEXT("/Game/Characters/Soldier/Animations/BS_SoldierLocomotion.BS_SoldierLocomotion"));
	if (LocomotionFinder.Succeeded())
	{
		LocomotionAsset = LocomotionFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<USoundWave> FireSoundFinder(
		TEXT("/Game/Weapons/M416/Audio/S_M416_Fire.S_M416_Fire"));
	if (FireSoundFinder.Succeeded())
	{
		BotFireSound = FireSoundFinder.Object;
	}
}

void AHampiAICharacter::ConfigureAnimation()
{
	USkeletalMeshComponent* MeshComp = GetMesh();
	if (!MeshComp || !LocomotionAsset)
	{
		return;
	}

	MeshComp->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	MeshComp->PlayAnimation(LocomotionAsset, true);
	if (UAnimSingleNodeInstance* SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance()))
	{
		SingleNode->SetLooping(true);
		SingleNode->SetPlayRate(1.0f);
	}
}

void AHampiAICharacter::SetBotPersona(EHampiBotPersona InPersona)
{
	Persona = InPersona;
	ApplyPersonaStats();
}

void AHampiAICharacter::ApplyPersonaStats()
{
	switch (Persona)
	{
	case EHampiBotPersona::Raven:
		DisplayName = TEXT("Raven");
		MaxHealth = 80.0f;
		SightRadius = 2400.0f;
		AttackRange = 850.0f;
		PreferredRange = 320.0f;
		FireInterval = 0.26f;
		AttackDamage = 6.0f;
		MaxLocomotionSpeed = 440.0f;
		PatrolRadius = 950.0f;
		break;
	case EHampiBotPersona::Shadow:
		DisplayName = TEXT("Shadow");
		MaxHealth = 70.0f;
		SightRadius = 4600.0f;
		AttackRange = 4200.0f;
		PreferredRange = 2300.0f;
		FireInterval = 1.35f;
		AttackDamage = 22.0f;
		MaxLocomotionSpeed = 300.0f;
		PatrolRadius = 2000.0f;
		break;
	case EHampiBotPersona::Hunter:
		DisplayName = TEXT("Hunter");
		MaxHealth = 110.0f;
		SightRadius = 3200.0f;
		AttackRange = 1600.0f;
		PreferredRange = 780.0f;
		FireInterval = 0.52f;
		AttackDamage = 9.0f;
		MaxLocomotionSpeed = 405.0f;
		PatrolRadius = 1700.0f;
		break;
	case EHampiBotPersona::Viper:
		DisplayName = TEXT("Viper");
		MaxHealth = 100.0f;
		SightRadius = 3600.0f;
		AttackRange = 2200.0f;
		PreferredRange = 1250.0f;
		FireInterval = 0.38f;
		AttackDamage = 8.0f;
		MaxLocomotionSpeed = 365.0f;
		PatrolRadius = 1500.0f;
		break;
	case EHampiBotPersona::Ghost:
		DisplayName = TEXT("Ghost");
		MaxHealth = 90.0f;
		SightRadius = 3000.0f;
		AttackRange = 1700.0f;
		PreferredRange = 1450.0f;
		FireInterval = 0.60f;
		AttackDamage = 7.0f;
		MaxLocomotionSpeed = 390.0f;
		PatrolRadius = 1800.0f;
		break;
	}

	CurrentHealth = MaxHealth;
	SpawnLocation = GetActorLocation();
	StrafeDirection = FMath::RandBool() ? 1.0f : -1.0f;
	GetCharacterMovement()->MaxWalkSpeed = MaxLocomotionSpeed;

	ConfigureAnimation();
	ChoosePatrolPoint();
}

void AHampiAICharacter::BeginPlay()
{
	Super::BeginPlay();
	ApplyPersonaStats();
}

void AHampiAICharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!IsBotAlive())
	{
		return;
	}

	UpdateAnimation(DeltaSeconds);
	DetectPlayer();
	UpdateState();
	Move(DeltaSeconds);
	TryFire();

	if (Persona == EHampiBotPersona::Ghost && CurrentHealth < MaxHealth &&
		GetWorld()->GetTimeSeconds() >= NextHealTime)
	{
		CurrentHealth = FMath::Min(MaxHealth, CurrentHealth + 6.0f);
		NextHealTime = GetWorld()->GetTimeSeconds() + 2.5f;
	}
}

void AHampiAICharacter::UpdateAnimation(float DeltaSeconds)
{
	USkeletalMeshComponent* MeshComp = GetMesh();
	if (!MeshComp)
	{
		return;
	}

	UAnimSingleNodeInstance* SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance());
	if (!SingleNode)
	{
		ConfigureAnimation();
		SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance());
		if (!SingleNode)
		{
			return;
		}
	}

	const FVector Velocity = GetVelocity();
	const float Speed = FVector(Velocity.X, Velocity.Y, 0.0f).Size();
	SingleNode->SetBlendSpacePosition(FVector(
		FMath::Clamp(Speed, 0.0f, FMath::Max(1.0f, MaxLocomotionSpeed)), 0.0f, 0.0f));
}

void AHampiAICharacter::DetectPlayer()
{
	const float Now = GetWorld()->GetTimeSeconds();
	if (Now < NextDetectionTime)
	{
		return;
	}
	NextDetectionTime = Now + 0.20f;

	AHampiSoldierCharacter* Player = Cast<AHampiSoldierCharacter>(
		UGameplayStatics::GetPlayerCharacter(this, 0));
	if (!Player || !Player->IsValidLowLevel())
	{
		return;
	}

	const float Distance = FVector::Dist(GetActorLocation(), Player->GetActorLocation());
	if (Distance <= SightRadius && HasLineOfSight(Player))
	{
		TargetPlayer = Player;
		LastKnownPlayerLocation = Player->GetActorLocation();
		LastSeenTime = Now;
	}
}

void AHampiAICharacter::UpdateState()
{
	if (!TargetPlayer || !IsValid(TargetPlayer))
	{
		CurrentState = EHampiBotState::Patrol;
		return;
	}

	const float Distance = FVector::Dist(GetActorLocation(), TargetPlayer->GetActorLocation());
	if (Persona == EHampiBotPersona::Ghost && Distance < PreferredRange * 0.65f)
	{
		CurrentState = EHampiBotState::Retreat;
		return;
	}

	if (Distance <= SightRadius && HasLineOfSight(TargetPlayer))
	{
		CurrentState = EHampiBotState::Engage;
		return;
	}

	if (GetWorld()->GetTimeSeconds() - LastSeenTime < 4.0f)
	{
		CurrentState = EHampiBotState::Investigate;
	}
	else
	{
		CurrentState = EHampiBotState::Patrol;
	}
}

void AHampiAICharacter::ChoosePatrolPoint()
{
	const float Angle = FMath::RandRange(0.0f, 2.0f * PI);
	const float Radius = FMath::RandRange(PatrolRadius * 0.35f, PatrolRadius);
	PatrolTarget = SpawnLocation + FVector(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, 0.0f);
	NextPatrolTime = GetWorld() ? GetWorld()->GetTimeSeconds() + FMath::RandRange(3.0f, 6.0f) : 0.0f;
}

void AHampiAICharacter::Move(float DeltaSeconds)
{
	FVector DesiredDirection = FVector::ZeroVector;
	const FVector MyLocation = GetActorLocation();

	if (CurrentState == EHampiBotState::Patrol)
	{
		if (GetWorld()->GetTimeSeconds() >= NextPatrolTime || FVector::Dist(MyLocation, PatrolTarget) < 120.0f)
		{
			ChoosePatrolPoint();
		}
		DesiredDirection = PatrolTarget - MyLocation;
	}
	else if (CurrentState == EHampiBotState::Investigate)
	{
		DesiredDirection = LastKnownPlayerLocation - MyLocation;
		if (FVector::Dist(MyLocation, LastKnownPlayerLocation) < 150.0f)
		{
			CurrentState = EHampiBotState::Patrol;
			ChoosePatrolPoint();
		}
	}
	else if (TargetPlayer && CurrentState == EHampiBotState::Engage)
	{
		const FVector ToPlayer = TargetPlayer->GetActorLocation() - MyLocation;
		const float Distance = ToPlayer.Size();
		const FVector Forward = ToPlayer.GetSafeNormal();
		const FVector Right = FVector::CrossProduct(FVector::UpVector, Forward).GetSafeNormal();

		if (Distance > PreferredRange * 1.15f)
		{
			DesiredDirection = Forward;
		}
		else if (Persona == EHampiBotPersona::Shadow || Persona == EHampiBotPersona::Ghost)
		{
			if (Distance < PreferredRange * 0.80f)
			{
				DesiredDirection = -Forward;
			}
			else
			{
				DesiredDirection = Right * StrafeDirection;
			}
		}
		else
		{
			DesiredDirection = Right * StrafeDirection;
		}
	}
	else if (TargetPlayer && CurrentState == EHampiBotState::Retreat)
	{
		DesiredDirection = MyLocation - TargetPlayer->GetActorLocation();
	}

	DesiredDirection.Z = 0.0f;
	DesiredDirection = DesiredDirection.GetSafeNormal();

	// Cheap obstacle nudge: if directly ahead is blocked, slide sideways.
	const FVector TraceStart = GetEyeLocation();
	const FVector TraceEnd = TraceStart + (DesiredDirection.IsNearlyZero()
		? GetActorForwardVector() : DesiredDirection) * 180.0f;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(HampiBotAvoid), false, this);
	FHitResult Obstacle;
	if (!DesiredDirection.IsNearlyZero() &&
		GetWorld()->LineTraceSingleByChannel(Obstacle, TraceStart, TraceEnd, ECC_Visibility, Params))
	{
		const FVector Slide = FVector::CrossProduct(FVector::UpVector, DesiredDirection).GetSafeNormal();
		DesiredDirection = (DesiredDirection * 0.25f + Slide * StrafeDirection).GetSafeNormal();
	}

	if (!DesiredDirection.IsNearlyZero())
	{
		AddMovementInput(DesiredDirection, 1.0f);
	}

	if (TargetPlayer && (CurrentState == EHampiBotState::Engage || CurrentState == EHampiBotState::Retreat))
	{
		const FVector ToPlayer = TargetPlayer->GetActorLocation() - MyLocation;
		const FRotator DesiredRotation(0.0f, ToPlayer.Rotation().Yaw, 0.0f);
		SetActorRotation(FMath::RInterpTo(GetActorRotation(), DesiredRotation, DeltaSeconds, 7.0f));
	}
	else if (!DesiredDirection.IsNearlyZero())
	{
		const FRotator DesiredRotation(0.0f, DesiredDirection.Rotation().Yaw, 0.0f);
		SetActorRotation(FMath::RInterpTo(GetActorRotation(), DesiredRotation, DeltaSeconds, 5.0f));
	}
}

void AHampiAICharacter::TryFire()
{
	const float Now = GetWorld()->GetTimeSeconds();
	if (CurrentState != EHampiBotState::Engage || !TargetPlayer || Now < NextFireTime)
	{
		return;
	}

	const float Distance = FVector::Dist(GetActorLocation(), TargetPlayer->GetActorLocation());
	if (Distance > AttackRange || !HasLineOfSight(TargetPlayer))
	{
		return;
	}

	const FVector Start = GetEyeLocation();
	const FVector Target = GetPlayerChestLocation(TargetPlayer);
	FVector Direction = (Target - Start).GetSafeNormal();
	const float Spread = Persona == EHampiBotPersona::Shadow ? 0.25f : 1.4f;
	Direction = FRotator(FMath::FRandRange(-Spread, Spread), FMath::FRandRange(-Spread, Spread), 0.0f)
		.RotateVector(Direction).GetSafeNormal();

	const FVector End = Start + Direction * AttackRange;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(HampiBotFire), false, this);
	FHitResult Hit;
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, Params) &&
		Hit.GetActor() == TargetPlayer)
	{
		UGameplayStatics::ApplyDamage(TargetPlayer, AttackDamage, GetController(), this,
			UDamageType::StaticClass());
	}

	if (BotFireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, BotFireSound, Start, 0.35f);
	}

	NextFireTime = Now + FireInterval + FMath::FRandRange(0.0f, 0.12f);
	if (FMath::RandBool())
	{
		StrafeDirection *= -1.0f;
	}
}

FVector AHampiAICharacter::GetEyeLocation() const
{
	return GetActorLocation() + FVector(0.0f, 0.0f, GetCapsuleComponent()->GetScaledCapsuleHalfHeight() * 0.65f);
}

FVector AHampiAICharacter::GetPlayerChestLocation(const AHampiSoldierCharacter* Player) const
{
	return Player ? Player->GetActorLocation() + FVector(0.0f, 0.0f, 65.0f) : FVector::ZeroVector;
}

bool AHampiAICharacter::HasLineOfSight(const AHampiSoldierCharacter* Player) const
{
	if (!Player)
	{
		return false;
	}

	FCollisionQueryParams Params(SCENE_QUERY_STAT(HampiBotSight), false, this);
	FHitResult Hit;
	const bool bHit = GetWorld()->LineTraceSingleByChannel(
		Hit, GetEyeLocation(), GetPlayerChestLocation(Player), ECC_Pawn, Params);
	return bHit && Hit.GetActor() == Player;
}

float AHampiAICharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	const float Applied = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	if (Applied <= 0.0f || !IsBotAlive())
	{
		return Applied;
	}

	CurrentHealth = FMath::Max(0.0f, CurrentHealth - Applied);
	if (CurrentHealth <= 0.0f)
	{
		Die();
	}
	return Applied;
}

void AHampiAICharacter::ApplyTestDamage(float Amount)
{
	FDamageEvent Event;
	TakeDamage(FMath::Max(0.0f, Amount), Event, nullptr, this);
}

void AHampiAICharacter::Die()
{
	CurrentHealth = 0.0f;
	CurrentState = EHampiBotState::Patrol;
	TargetPlayer = nullptr;
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GetMesh()->SetSimulatePhysics(true);
	DetachFromControllerPendingDestroy();
	SetLifeSpan(4.0f);
}

FString AHampiAICharacter::GetBotStateName() const
{
	switch (CurrentState)
	{
	case EHampiBotState::Patrol: return TEXT("Patrol");
	case EHampiBotState::Investigate: return TEXT("Investigate");
	case EHampiBotState::Engage: return TEXT("Engage");
	case EHampiBotState::Retreat: return TEXT("Retreat");
	default: return TEXT("Unknown");
	}
}
