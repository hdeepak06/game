#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "HampiSoldierCharacter.generated.h"

class UAnimationAsset;
class UInputAction;
class AM416Weapon;
class AHampiDialogueDirector;
class UHampiMobileHUDWidget;

/** One stack in the lightweight battle-royale inventory. */
USTRUCT(BlueprintType)
struct FHampiInventoryEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Inventory")
	FString ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Inventory")
	int32 Quantity = 0;
};

/**
 * Keeps the existing third-person character behaviour intact while driving the
 * imported soldier locomotion through a lightweight SingleNode blend space.
 * Also owns the single optional M416 weapon without changing movement/camera.
 */
UCLASS()
class BATTLEGROUND_API AHampiSoldierCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AHampiSoldierCharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		class AController* EventInstigator, AActor* DamageCauser) override;

	/** Player health/shield model. Damage hits shield first, then health. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi Player|Health", meta = (ClampMin = "1.0"))
	float MaxPlayerHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Player|Health")
	float CurrentPlayerHealth = 100.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi Player|Health", meta = (ClampMin = "0.0"))
	float MaxPlayerShield = 50.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Player|Health")
	float CurrentPlayerShield = 0.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi Player|Health", meta = (ClampMin = "0.0"))
	float HealthRegenDelay = 8.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi Player|Health", meta = (ClampMin = "0.0"))
	float HealthRegenPerSecond = 3.0f;

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	float GetCurrentPlayerHealth() const { return CurrentPlayerHealth; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	float GetMaxPlayerHealth() const { return MaxPlayerHealth; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	float GetCurrentPlayerShield() const { return CurrentPlayerShield; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	float GetMaxPlayerShield() const { return MaxPlayerShield; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	float GetHealthFraction() const { return MaxPlayerHealth > 0.0f ? CurrentPlayerHealth / MaxPlayerHealth : 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	bool IsPlayerAlive() const { return CurrentPlayerHealth > 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	bool IsHealing() const { return HealRemaining > 0.0f; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Health")
	FString GetLastDamageSource() const { return LastDamageSource; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	bool IsPlayerCrouched() const { return bIsCrouched; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	bool IsPlayerAirborne() const;

	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Movement")
	void MobileJump();

	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Movement")
	void MobileStopJump();

	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Movement")
	void TogglePlayerCrouch();

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	int32 GetMobileJumpCallCount() const { return MobileJumpCallCount; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	bool WasLastMobileJumpAllowed() const { return bLastMobileJumpAllowed; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	bool DidLastMobileJumpLaunch() const { return bLastMobileJumpLaunched; }

	UFUNCTION(BlueprintPure, Category = "Hampi Player|Movement")
	float GetLastMobileJumpLaunchZ() const { return LastMobileJumpLaunchZ; }

	/** Instant heal, capped at MaxPlayerHealth. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Health")
	void Heal(float Amount);

	/** Restores Amount evenly over Duration seconds (energy drink). */
	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Health")
	void StartHealOverTime(float Amount, float Duration);

	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Health")
	void AddShield(float Amount);

	/** Test/diagnostic damage entry point. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Health")
	void ApplyTestDamage(float Amount);

	/** Restores full health/shield at the preserved PlayerStart. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Player|Health")
	void Respawn();

	/** Adds a loot stack to the inventory. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Inventory")
	bool AddInventoryItem(const FString& ItemId, int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Hampi Inventory")
	int32 GetInventoryCount(const FString& ItemId) const;

	/** Uses a stored consumable (Medkit, EnergyDrink or Armor). */
	UFUNCTION(BlueprintCallable, Category = "Hampi Inventory")
	bool UseConsumable(const FString& ItemId);

	UFUNCTION(BlueprintPure, Category = "Hampi Inventory")
	FString GetInventorySummary() const;

	/** Assigns an item id to Primary, Secondary or Pistol. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Inventory")
	void SetWeaponSlot(const FString& SlotName, const FString& ItemId);

	UFUNCTION(BlueprintPure, Category = "Hampi Inventory")
	FString GetWeaponSlot(const FString& SlotName) const;

	/** Cycles Primary -> Secondary -> Pistol for the mobile SWAP button. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Inventory")
	void CycleWeaponSlot();

	UFUNCTION(BlueprintPure, Category = "Hampi Inventory")
	FString GetActiveWeaponSlot() const { return ActiveWeaponSlot; }

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Inventory")
	FString ActiveWeaponSlot = TEXT("Primary");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Inventory")
	TArray<FHampiInventoryEntry> Inventory;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Inventory")
	FString PrimaryWeaponSlot = TEXT("None");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Inventory")
	FString SecondaryWeaponSlot = TEXT("None");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi Inventory")
	FString PistolWeaponSlot = TEXT("None");

	/** Blend space containing idle/walk/run samples for the soldier skeleton. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Soldier")
	TObjectPtr<UAnimationAsset> LocomotionAsset;

	/** Speed in cm/s that maps to the far end of the locomotion blend space. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Soldier", meta = (ClampMin = "1.0"))
	float MaxLocomotionSpeed = 450.0f;

	/** Drives the blend space input every frame from horizontal velocity. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hampi Soldier")
	bool bDriveLocomotionAnimation = true;

	/** The single M416 currently carried by this soldier, if any. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416")
	TObjectPtr<AM416Weapon> EquippedM416;

	/** True while the aim input is held. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416")
	bool bIsAimingM416 = false;

	/** Equips a world M416. Only one weapon can be carried. */
	UFUNCTION(BlueprintCallable, Category = "M416")
	void EquipM416(AM416Weapon* Weapon);

	/** Picks up the nearest unequipped M416 within PickupRange. */
	UFUNCTION(BlueprintCallable, Category = "M416")
	bool TryPickupM416();

	UFUNCTION(BlueprintCallable, Category = "M416")
	void StartM416Fire();

	UFUNCTION(BlueprintCallable, Category = "M416")
	void StopM416Fire();

	UFUNCTION(BlueprintCallable, Category = "M416")
	void StartM416Aim();

	UFUNCTION(BlueprintCallable, Category = "M416")
	void StopM416Aim();

	UFUNCTION(BlueprintCallable, Category = "M416")
	void ReloadM416();

	UFUNCTION(BlueprintPure, Category = "M416")
	bool IsAimingM416() const { return bIsAimingM416; }

	/** Python-safe alias because the bIsAimingM416 UPROPERTY occupies the snake_case name. */
	UFUNCTION(BlueprintPure, Category = "M416")
	bool IsAimingM416Active() const { return bIsAimingM416; }

	/** The native mobile HUD created once at BeginPlay; exposed for PIE verification. */
	UFUNCTION(BlueprintPure, Category = "Hampi HUD")
	UHampiMobileHUDWidget* GetMobileHUDWidget() const { return MobileHUDWidget; }

	/** Radius used by the E-key fallback pickup. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416", meta = (ClampMin = "50.0"))
	float M416PickupRange = 280.0f;

private:
	void ConfigureSoldierAnimation();
	void HandlePickupInput();
	void ReplaceM416PickupMarker();
	void SpawnAIBots();
	void SpawnSafeZone();
	void SpawnHealingItems();
	void SpawnLootItems();
	void SpawnDialogueDirector();
	void SpawnMobileHUD();
	void PlayDialogueCue(const FString& CueName);
	void TickHealth(float DeltaSeconds);
	void Die(const FString& KillerName);

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> M416FireAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> M416AimAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> M416ReloadAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> M416PickupAction;

	UPROPERTY(Transient)
	TObjectPtr<UHampiMobileHUDWidget> MobileHUDWidget;

	float SavedCameraFOV = 0.0f;
	float AimCameraFOV = 55.0f;

	float LastDamageTime = -1000.0f;
	float HealRemaining = 0.0f;
	float HealPerSecond = 0.0f;
	FString LastDamageSource = TEXT("None");
	int32 MobileJumpCallCount = 0;
	bool bLastMobileJumpAllowed = false;
	bool bLastMobileJumpLaunched = false;
	float LastMobileJumpLaunchZ = 0.0f;
};
