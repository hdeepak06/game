#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HampiLootItem.generated.h"

class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EHampiLootType : uint8
{
	Ammo556,
	Medkit,
	EnergyDrink,
	Armor
};

/** Reusable ground loot with a glowing marker and proximity pickup. */
UCLASS()
class BATTLEGROUND_API AHampiLootItem : public AActor
{
	GENERATED_BODY()

public:
	AHampiLootItem();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Loot")
	EHampiLootType LootType = EHampiLootType::Ammo556;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Loot", meta = (ClampMin = "1"))
	int32 Amount = 30;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Loot", meta = (ClampMin = "50.0"))
	float PickupRadius = 180.0f;

	UFUNCTION(BlueprintPure, Category = "Hampi Loot")
	FString GetLootTypeId() const;

	UFUNCTION(BlueprintPure, Category = "Hampi Loot")
	FString GetLootDisplayName() const;

	UFUNCTION(BlueprintPure, Category = "Hampi Loot")
	int32 GetLootAmount() const { return Amount; }

	UFUNCTION(BlueprintPure, Category = "Hampi Loot")
	bool IsAvailable() const { return bAvailable; }

private:
	void TryPickup();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> Marker;

	bool bAvailable = true;
};
