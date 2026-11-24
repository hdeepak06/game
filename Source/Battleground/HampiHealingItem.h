#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HampiHealingItem.generated.h"

class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EHampiHealingItemType : uint8
{
	Medkit,
	EnergyDrink,
	Armor
};

/** Simple one-use world pickup used by the health/healing phase. */
UCLASS()
class BATTLEGROUND_API AHampiHealingItem : public AActor
{
	GENERATED_BODY()

public:
	AHampiHealingItem();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Health")
	EHampiHealingItemType ItemType = EHampiHealingItemType::Medkit;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Health", meta = (ClampMin = "1.0"))
	float HealAmount = 50.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Health", meta = (ClampMin = "50.0"))
	float PickupRadius = 170.0f;

	UFUNCTION(BlueprintPure, Category = "Hampi Health")
	FString GetItemTypeName() const;

	UFUNCTION(BlueprintPure, Category = "Hampi Health")
	float GetHealAmount() const { return HealAmount; }

	UFUNCTION(BlueprintPure, Category = "Hampi Health")
	bool IsAvailable() const { return bAvailable; }

private:
	void TryPickup();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Mesh;

	bool bAvailable = true;
};
