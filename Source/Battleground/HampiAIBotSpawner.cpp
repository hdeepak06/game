#include "HampiAIBotSpawner.h"

#include "HampiAICharacter.h"

#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"

AHampiAIBotSpawner::AHampiAIBotSpawner()
{
	PrimaryActorTick.bCanEverTick = false;
}

FVector AHampiAIBotSpawner::ResolveGroundLocation(const FVector& Requested, float ReferenceZ) const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return Requested;
	}

	const FVector TraceStart(Requested.X, Requested.Y, Requested.Z + 2500.0f);
	const FVector TraceEnd(Requested.X, Requested.Y, Requested.Z - 3500.0f);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(HampiBotGround), false, this);
	FHitResult Hit;
	if (World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
	{
		// Character capsule half height is 96 cm; add a small safety margin.
		return Hit.Location + FVector(0.0f, 0.0f, 102.0f);
	}
	return FVector(Requested.X, Requested.Y, ReferenceZ + 250.0f);
}

void AHampiAIBotSpawner::BeginPlay()
{
	Super::BeginPlay();

	const ACharacter* Player = Cast<ACharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
	const FVector PlayerLocation = Player ? Player->GetActorLocation() : GetActorLocation();

	// Offsets are relative to the preserved PlayerStart at the landscape centre.
	// They spread the five bots across distinct ranges and approach angles.
	struct FBotDefinition
	{
		EHampiBotPersona Persona;
		FVector2D Offset;
	};

	const FBotDefinition Definitions[] =
	{
		{ EHampiBotPersona::Raven,  FVector2D(  900.0f,   650.0f) },
		{ EHampiBotPersona::Shadow, FVector2D(-2600.0f,  1850.0f) },
		{ EHampiBotPersona::Hunter, FVector2D( 2050.0f, -1800.0f) },
		{ EHampiBotPersona::Viper,  FVector2D(-1550.0f, -2450.0f) },
		{ EHampiBotPersona::Ghost,  FVector2D( 3050.0f,  1250.0f) }
	};

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.Owner = this;

	for (const FBotDefinition& Definition : Definitions)
	{
		const FVector Requested(
			PlayerLocation.X + Definition.Offset.X,
			PlayerLocation.Y + Definition.Offset.Y,
			PlayerLocation.Z);
		const FVector SpawnLocation = ResolveGroundLocation(Requested, PlayerLocation.Z);

		AHampiAICharacter* Bot = GetWorld()->SpawnActor<AHampiAICharacter>(
			AHampiAICharacter::StaticClass(), SpawnLocation, FRotator::ZeroRotator, Params);
		if (Bot)
		{
			// BeginPlay has already run with the default persona, so re-apply stats here.
			Bot->SetBotPersona(Definition.Persona);
			SpawnedBots.Add(Bot);
		}
	}
}

int32 AHampiAIBotSpawner::GetSpawnedBotCount() const
{
	return SpawnedBots.Num();
}

TArray<AHampiAICharacter*> AHampiAIBotSpawner::GetSpawnedBots() const
{
	TArray<AHampiAICharacter*> Result;
	for (AHampiAICharacter* Bot : SpawnedBots)
	{
		Result.Add(Bot);
	}
	return Result;
}
