#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HampiAIBotSpawner.generated.h"

class AHampiAICharacter;

/**
 * Spawns the five named battle-royale enemies once when the player begins play.
 * Created at runtime by the player soldier so the saved map stays untouched.
 */
UCLASS()
class BATTLEGROUND_API AHampiAIBotSpawner : public AActor
{
	GENERATED_BODY()

public:
	AHampiAIBotSpawner();

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintPure, Category = "Hampi AI|Spawner")
	int32 GetSpawnedBotCount() const;

	UFUNCTION(BlueprintPure, Category = "Hampi AI|Spawner")
	TArray<AHampiAICharacter*> GetSpawnedBots() const;

private:
	FVector ResolveGroundLocation(const FVector& Requested, float ReferenceZ) const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<AHampiAICharacter>> SpawnedBots;
};
