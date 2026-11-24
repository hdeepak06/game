#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "M416Weapon.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class USphereComponent;
class USoundWave;
class UPrimitiveComponent;
class AHampiSoldierCharacter;

/**
 * The one M416 rifle used in the project. It is a world pickup until a soldier
 * overlaps it or presses the pickup key, then it attaches to the right hand and
 * provides aiming, automatic fire, recoil, trace damage, ammo and reload.
 */
UCLASS()
class BATTLEGROUND_API AM416Weapon : public AActor
{
	GENERATED_BODY()

public:
	AM416Weapon();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|Components")
	TObjectPtr<USphereComponent> PickupSphere;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|Components")
	TObjectPtr<UStaticMeshComponent> WeaponMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|Components")
	TObjectPtr<UStaticMeshComponent> MuzzleFlashMesh;

	/** Uniform scale applied to the imported FBX to convert it to a normal rifle. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.01"))
	float WeaponScale = 0.11f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning")
	int32 MagazineSize = 30;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning")
	int32 StartingReserveAmmo = 120;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.01"))
	float FireInterval = 0.095f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.01"))
	float ReloadTime = 1.8f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "100.0"))
	float WeaponRange = 8000.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.0"))
	float FireDamage = 24.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.0"))
	float HipSpreadDegrees = 1.35f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Tuning", meta = (ClampMin = "0.0"))
	float AimSpreadDegrees = 0.18f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Audio")
	TObjectPtr<USoundWave> FireSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "M416|Audio")
	TObjectPtr<USoundWave> ReloadSound;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|State")
	int32 CurrentAmmo = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|State")
	int32 ReserveAmmo = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "M416|State")
	bool bReloading = false;

	bool IsEquipped() const { return bEquipped; }

	void EquipTo(AHampiSoldierCharacter* Character);
	void SetTriggerDown(bool bDown);
	void SetAiming(bool bAim);
	void Reload();

	UFUNCTION(BlueprintPure, Category = "M416|State")
	int32 GetCurrentAmmo() const { return CurrentAmmo; }

	UFUNCTION(BlueprintPure, Category = "M416|State")
	int32 GetReserveAmmo() const { return ReserveAmmo; }

	UFUNCTION(BlueprintPure, Category = "M416|State")
	bool IsReloading() const { return bReloading; }

private:
	UFUNCTION()
	void HandlePickupOverlap(UPrimitiveComponent* OverlappedComponent,
		AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	AHampiSoldierCharacter* EquippedCharacter() const;
	void FireOnce();
	void FinishReload();
	void ApplyRecoil(float PitchAmount, float YawAmount);
	void RecoverRecoil(float DeltaSeconds);

	bool bEquipped = false;
	bool bTriggerDown = false;
	bool bAiming = false;
	bool bMuzzleFlashVisible = false;

	float NextFireTime = 0.0f;
	float ReloadFinishTime = 0.0f;
	float MuzzleFlashEndTime = 0.0f;
	float RecoilRecoveryStartTime = 0.0f;
	float PendingRecoilPitch = 0.0f;
	float PendingRecoilYaw = 0.0f;
};
