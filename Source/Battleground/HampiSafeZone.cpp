#include "HampiSafeZone.h"

#include "HampiAICharacter.h"
#include "HampiSoldierCharacter.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/DamageType.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

AHampiSafeZone::AHampiSafeZone()
{
	PrimaryActorTick.bCanEverTick = true;

	ZoneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ZoneRoot"));
	RootComponent = ZoneRoot;

	WallMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WallMesh"));
	WallMesh->SetupAttachment(ZoneRoot);
	WallMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WallMesh->SetCastShadow(false);
	WallMesh->SetCullDistance(30000.0f);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderFinder.Succeeded())
	{
		WallMesh->SetStaticMesh(CylinderFinder.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MaterialFinder(
		TEXT("/Game/Environment/SafeZone/M_SafeZoneWall.M_SafeZoneWall"));
	if (MaterialFinder.Succeeded())
	{
		WallMesh->SetMaterial(0, MaterialFinder.Object);
	}

	CurrentRadius = InitialRadius;
}

void AHampiSafeZone::BeginPlay()
{
	Super::BeginPlay();
	StartTime = GetWorld()->GetTimeSeconds();
	NextDamageTime = StartTime + 0.5f;
	CurrentRadius = InitialRadius;
	UpdateWall();
}

void AHampiSafeZone::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Now = GetWorld()->GetTimeSeconds();
	const float Elapsed = Now - StartTime;

	if (Elapsed <= ShrinkStartDelay)
	{
		CurrentRadius = InitialRadius;
		CurrentPhase = 0;
	}
	else
	{
		const float Timeline = FMath::Max(1.0f, PhaseDuration + TimeBetweenPhases);
		const int32 Completed = FMath::FloorToInt((Elapsed - ShrinkStartDelay) / Timeline);
		if (Completed >= PhaseCount)
		{
			CurrentRadius = FinalRadius;
			CurrentPhase = PhaseCount;
		}
		else
		{
			const float Within = FMath::Fmod(Elapsed - ShrinkStartDelay, Timeline);
			const float Alpha = FMath::Clamp(Within / PhaseDuration, 0.0f, 1.0f);
			const float StartR = FMath::Lerp(InitialRadius, FinalRadius,
				static_cast<float>(Completed) / static_cast<float>(PhaseCount));
			const float EndR = FMath::Lerp(InitialRadius, FinalRadius,
				static_cast<float>(Completed + 1) / static_cast<float>(PhaseCount));
			CurrentRadius = FMath::Lerp(StartR, EndR, Alpha);
			CurrentPhase = Completed + 1;
		}
	}

	UpdateWall();

	if (Now >= NextDamageTime)
	{
		NextDamageTime = Now + 0.5f;
		ApplyZoneDamage(ZoneDamagePerSecond * 0.5f);
	}
}

float AHampiSafeZone::GetTimeToNextPhase() const
{
	const float Elapsed = GetWorld() ? GetWorld()->GetTimeSeconds() - StartTime : 0.0f;
	if (Elapsed <= ShrinkStartDelay)
	{
		return ShrinkStartDelay - Elapsed;
	}
	const float Timeline = FMath::Max(1.0f, PhaseDuration + TimeBetweenPhases);
	const float Within = FMath::Fmod(Elapsed - ShrinkStartDelay, Timeline);
	return Within <= PhaseDuration ? PhaseDuration - Within : Timeline - Within;
}

bool AHampiSafeZone::IsInside(const FVector& Location) const
{
	const FVector Delta = Location - GetActorLocation();
	return FVector(Delta.X, Delta.Y, 0.0f).Size() <= CurrentRadius;
}

void AHampiSafeZone::UpdateWall()
{
	if (!WallMesh)
	{
		return;
	}

	// /Engine/BasicShapes/Cylinder is 100 cm tall with a 50 cm radius.
	const float Height = 4000.0f;
	WallMesh->SetRelativeLocation(FVector(0.0f, 0.0f, Height * 0.5f - 250.0f));
	WallMesh->SetRelativeScale3D(FVector(
		FMath::Max(1.0f, CurrentRadius) / 50.0f,
		FMath::Max(1.0f, CurrentRadius) / 50.0f,
		Height / 100.0f));
}

void AHampiSafeZone::ApplyZoneDamage(float DamageAmount)
{
	if (DamageAmount <= 0.0f)
	{
		return;
	}

	for (TActorIterator<AHampiSoldierCharacter> It(GetWorld()); It; ++It)
	{
		AHampiSoldierCharacter* Player = *It;
		if (Player && Player->IsPlayerAlive() && !IsInside(Player->GetActorLocation()))
		{
			UGameplayStatics::ApplyDamage(Player, DamageAmount, nullptr, this,
				UDamageType::StaticClass());
		}
	}

	for (TActorIterator<AHampiAICharacter> It(GetWorld()); It; ++It)
	{
		AHampiAICharacter* Bot = *It;
		if (Bot && Bot->IsBotAlive() && !IsInside(Bot->GetActorLocation()))
		{
			UGameplayStatics::ApplyDamage(Bot, DamageAmount, nullptr, this,
				UDamageType::StaticClass());
		}
	}
}
