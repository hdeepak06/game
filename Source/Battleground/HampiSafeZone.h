#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HampiSafeZone.generated.h"

class USceneComponent;
class UStaticMeshComponent;

/**
 * Mobile-friendly shrinking battle-royale zone. A single additive cylinder wall
 * shows the boundary; actors outside it take periodic damage. Created at runtime
 * so the saved map is unchanged.
 */
UCLASS()
class BATTLEGROUND_API AHampiSafeZone : public AActor
{
	GENERATED_BODY()

public:
	AHampiSafeZone();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "100.0"))
	float InitialRadius = 24000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "100.0"))
	float FinalRadius = 1500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "0.0"))
	float ShrinkStartDelay = 45.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "1.0"))
	float PhaseDuration = 60.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "0.0"))
	float TimeBetweenPhases = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "1"))
	int32 PhaseCount = 4;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hampi Safe Zone", meta = (ClampMin = "0.0"))
	float ZoneDamagePerSecond = 6.0f;

	UFUNCTION(BlueprintPure, Category = "Hampi Safe Zone")
	float GetCurrentRadius() const { return CurrentRadius; }

	UFUNCTION(BlueprintPure, Category = "Hampi Safe Zone")
	int32 GetPhase() const { return CurrentPhase; }

	UFUNCTION(BlueprintPure, Category = "Hampi Safe Zone")
	float GetTimeToNextPhase() const;

	UFUNCTION(BlueprintPure, Category = "Hampi Safe Zone")
	bool IsInside(const FVector& Location) const;

private:
	void UpdateWall();
	void ApplyZoneDamage(float DamageAmount);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> ZoneRoot;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> WallMesh;

	float StartTime = 0.0f;
	float CurrentRadius = 0.0f;
	int32 CurrentPhase = 0;
	float NextDamageTime = 0.0f;
};
