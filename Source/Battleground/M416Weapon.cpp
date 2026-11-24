#include "M416Weapon.h"

#include "HampiSoldierCharacter.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/SceneComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/DamageType.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundWave.h"
#include "UObject/ConstructorHelpers.h"

AM416Weapon::AM416Weapon()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	PickupSphere = CreateDefaultSubobject<USphereComponent>(TEXT("PickupSphere"));
	PickupSphere->SetupAttachment(Root);
	PickupSphere->SetSphereRadius(115.0f);
	PickupSphere->SetCollisionProfileName(TEXT("OverlapOnlyPawn"));
	PickupSphere->SetGenerateOverlapEvents(true);
	PickupSphere->SetHiddenInGame(true);

	WeaponMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeaponMesh"));
	WeaponMesh->SetupAttachment(Root);
	WeaponMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WeaponMesh->SetCastShadow(false);
	WeaponMesh->SetCullDistance(6000.0f);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> RifleFinder(
		TEXT("/Game/Weapons/M416/SM_M416.SM_M416"));
	if (RifleFinder.Succeeded())
	{
		WeaponMesh->SetStaticMesh(RifleFinder.Object);
	}
	// Scale the mesh, not the actor, so the pickup sphere and FX keep world-sized values.
	// The imported rifle is ~767 cm long along local X; 0.11 scale makes it ~84 cm.
	WeaponMesh->SetRelativeScale3D(FVector(WeaponScale));

	MuzzleFlashMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MuzzleFlashMesh"));
	MuzzleFlashMesh->SetupAttachment(Root);
	MuzzleFlashMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	MuzzleFlashMesh->SetCastShadow(false);
	MuzzleFlashMesh->SetCullDistance(3000.0f);
	MuzzleFlashMesh->SetHiddenInGame(true);
	MuzzleFlashMesh->SetRelativeLocation(FVector(43.0f, 0.0f, 0.0f));
	MuzzleFlashMesh->SetRelativeRotation(FRotator(90.0f, 0.0f, 0.0f));
	MuzzleFlashMesh->SetRelativeScale3D(FVector(0.13f, 0.13f, 0.20f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeFinder(
		TEXT("/Engine/BasicShapes/Cone.Cone"));
	if (ConeFinder.Succeeded())
	{
		MuzzleFlashMesh->SetStaticMesh(ConeFinder.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> FlashMaterialFinder(
		TEXT("/Game/Weapons/M416/Materials/M_M416_MuzzleFlash.M_M416_MuzzleFlash"));
	if (FlashMaterialFinder.Succeeded())
	{
		MuzzleFlashMesh->SetMaterial(0, FlashMaterialFinder.Object);
	}

	static ConstructorHelpers::FObjectFinder<USoundWave> FireSoundFinder(
		TEXT("/Game/Weapons/M416/Audio/S_M416_Fire.S_M416_Fire"));
	static ConstructorHelpers::FObjectFinder<USoundWave> ReloadSoundFinder(
		TEXT("/Game/Weapons/M416/Audio/S_M416_Reload.S_M416_Reload"));
	if (FireSoundFinder.Succeeded())
	{
		FireSound = FireSoundFinder.Object;
	}
	if (ReloadSoundFinder.Succeeded())
	{
		ReloadSound = ReloadSoundFinder.Object;
	}

	CurrentAmmo = MagazineSize;
	ReserveAmmo = StartingReserveAmmo;
}

void AM416Weapon::BeginPlay()
{
	Super::BeginPlay();

	PickupSphere->OnComponentBeginOverlap.AddDynamic(this, &AM416Weapon::HandlePickupOverlap);
}

void AM416Weapon::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bEquipped)
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();

	if (bReloading)
	{
		if (Now >= ReloadFinishTime)
		{
			FinishReload();
		}
	}
	else if (bTriggerDown && CurrentAmmo > 0 && Now >= NextFireTime)
	{
		FireOnce();
	}

	if (bMuzzleFlashVisible && Now >= MuzzleFlashEndTime)
	{
		MuzzleFlashMesh->SetHiddenInGame(true);
		bMuzzleFlashVisible = false;
	}

	RecoverRecoil(DeltaSeconds);
}

void AM416Weapon::HandlePickupOverlap(UPrimitiveComponent* OverlappedComponent,
	AActor* OtherActor, UPrimitiveComponent* OtherComp,
	int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bEquipped)
	{
		return;
	}

	AHampiSoldierCharacter* Character = Cast<AHampiSoldierCharacter>(OtherActor);
	if (Character)
	{
		Character->EquipM416(this);
	}
}

void AM416Weapon::EquipTo(AHampiSoldierCharacter* Character)
{
	if (bEquipped || !Character)
	{
		return;
	}
	if (Character->EquippedM416 && Character->EquippedM416 != this)
	{
		return;
	}

	bEquipped = true;
	SetOwner(Character);

	PickupSphere->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PickupSphere->SetGenerateOverlapEvents(false);

	AttachToComponent(Character->GetMesh(),
		FAttachmentTransformRules(EAttachmentRule::SnapToTarget, false),
		TEXT("RightHand"));

	// Small forward offset puts the grip at the right hand while the barrel points ahead.
	SetActorRelativeLocation(FVector(12.0f, 0.0f, 0.0f));
	SetActorRelativeRotation(FRotator(0.0f, 0.0f, 0.0f));

	Character->EquippedM416 = this;
}

void AM416Weapon::SetTriggerDown(bool bDown)
{
	bTriggerDown = bDown;
}

void AM416Weapon::SetAiming(bool bAim)
{
	bAiming = bAim;
}

void AM416Weapon::Reload()
{
	if (!bEquipped || bReloading || CurrentAmmo >= MagazineSize || ReserveAmmo <= 0)
	{
		return;
	}

	bReloading = true;
	bTriggerDown = false;
	ReloadFinishTime = GetWorld()->GetTimeSeconds() + ReloadTime;

	if (ReloadSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ReloadSound, GetActorLocation(), 0.6f);
	}
}

void AM416Weapon::FinishReload()
{
	const int32 Needed = MagazineSize - CurrentAmmo;
	const int32 Loaded = FMath::Min(Needed, ReserveAmmo);
	CurrentAmmo += Loaded;
	ReserveAmmo -= Loaded;
	bReloading = false;
}

void AM416Weapon::FireOnce()
{
	if (CurrentAmmo <= 0 || bReloading || !EquippedCharacter())
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();
	CurrentAmmo--;
	NextFireTime = Now + FireInterval;

	MuzzleFlashMesh->SetHiddenInGame(false);
	bMuzzleFlashVisible = true;
	MuzzleFlashEndTime = Now + 0.045f;

	if (FireSound)
	{
		UGameplayStatics::PlaySoundAtLocation(
			this, FireSound, MuzzleFlashMesh->GetComponentLocation(), 0.55f);
	}

	APlayerController* PC = Cast<APlayerController>(EquippedCharacter()->GetController());
	FVector TraceStart = EquippedCharacter()->GetActorLocation() + FVector(0.0f, 0.0f, 70.0f);
	FVector TraceDirection = EquippedCharacter()->GetActorForwardVector();

	if (PC && PC->PlayerCameraManager)
	{
		TraceStart = PC->PlayerCameraManager->GetCameraLocation();
		TraceDirection = PC->PlayerCameraManager->GetCameraRotation().Vector();
	}

	const float Spread = bAiming ? AimSpreadDegrees : HipSpreadDegrees;
	const FRotator SpreadRotation(
		FMath::FRandRange(-Spread, Spread),
		FMath::FRandRange(-Spread, Spread),
		0.0f);
	TraceDirection = SpreadRotation.RotateVector(TraceDirection).GetSafeNormal();

	const FVector TraceEnd = TraceStart + TraceDirection * WeaponRange;

	FCollisionQueryParams Params;
	Params.AddIgnoredActor(EquippedCharacter());
	Params.AddIgnoredActor(this);

	FHitResult Hit;
	// Pawn profile ignores the Visibility channel by default, so use Pawn to hit characters.
	if (GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Pawn, Params))
	{
		AActor* HitActor = Hit.GetActor();
		if (HitActor && HitActor != EquippedCharacter())
		{
			UGameplayStatics::ApplyDamage(
				HitActor, FireDamage, EquippedCharacter()->GetController(),
				this, UDamageType::StaticClass());
		}
	}

	ApplyRecoil(0.65f, FMath::FRandRange(-0.24f, 0.24f));
}

AHampiSoldierCharacter* AM416Weapon::EquippedCharacter() const
{
	return Cast<AHampiSoldierCharacter>(GetOwner());
}

void AM416Weapon::ApplyRecoil(float PitchAmount, float YawAmount)
{
	APlayerController* PC = Cast<APlayerController>(
		EquippedCharacter() ? EquippedCharacter()->GetController() : nullptr);
	if (PC)
	{
		PC->SetControlRotation(PC->GetControlRotation() + FRotator(PitchAmount, YawAmount, 0.0f));
	}

	// Hold the kick briefly before recovering so it remains visible at low frame rates.
	RecoilRecoveryStartTime = GetWorld()->GetTimeSeconds() + 0.12f;
	PendingRecoilPitch += FMath::Abs(PitchAmount);
	PendingRecoilYaw += YawAmount;
}

void AM416Weapon::RecoverRecoil(float DeltaSeconds)
{
	if (PendingRecoilPitch <= 0.0f && FMath::IsNearlyZero(PendingRecoilYaw))
	{
		return;
	}

	APlayerController* PC = Cast<APlayerController>(
		EquippedCharacter() ? EquippedCharacter()->GetController() : nullptr);
	if (!PC || GetWorld()->GetTimeSeconds() < RecoilRecoveryStartTime)
	{
		return;
	}

	const float PitchStep = FMath::Min(PendingRecoilPitch, DeltaSeconds * 3.5f);
	const float YawStep = FMath::Min(FMath::Abs(PendingRecoilYaw), DeltaSeconds * 2.0f)
		* FMath::Sign(PendingRecoilYaw);

	PC->SetControlRotation(PC->GetControlRotation() - FRotator(PitchStep, YawStep, 0.0f));
	PendingRecoilPitch = FMath::Max(0.0f, PendingRecoilPitch - PitchStep);
	PendingRecoilYaw -= YawStep;
}
