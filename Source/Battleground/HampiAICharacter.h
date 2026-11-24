#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "HampiAICharacter.generated.h"

class UAnimationAsset;
class USoundWave;
class AHampiSoldierCharacter;

UENUM(BlueprintType)
enum class EHampiBotPersona : uint8
{
	Raven	UMETA(DisplayName = "Raven - Aggressive Flanker"),
	Shadow	UMETA(DisplayName = "Shadow - Stealth Sniper"),
	Hunter	UMETA(DisplayName = "Hunter - Patrol Tracker"),
	Viper	UMETA(DisplayName = "Viper - Assault Specialist"),
	Ghost	UMETA(DisplayName = "Ghost - Evasive Survivalist")
};

UENUM(BlueprintType)
enum class EHampiBotState : uint8
{
	Patrol		UMETA(DisplayName = "Patrol"),
	Investigate	UMETA(DisplayName = "Investigate"),
	Engage		UMETA(DisplayName = "Engage"),
	Retreat		UMETA(DisplayName = "Retreat")
};

/**
 * Lightweight, mobile-friendly battle-royale bot. It reuses the existing soldier
 * mesh/locomotion and uses direct steering plus periodic visibility traces instead
 * of a heavy Behavior Tree/navmesh dependency.
 */
UCLASS()
class BATTLEGROUND_API AHampiAICharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AHampiAICharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		class AController* EventInstigator, AActor* DamageCauser) override;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi AI|Identity")
	EHampiBotPersona Persona = EHampiBotPersona::Raven;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi AI|Identity")
	FString DisplayName = TEXT("Raven");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi AI|Animation")
	TObjectPtr<UAnimationAsset> LocomotionAsset;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi AI|Animation", meta = (ClampMin = "1.0"))
	float MaxLocomotionSpeed = 450.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi AI|Combat", meta = (ClampMin = "1.0"))
	float MaxHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi AI|Combat")
	float CurrentHealth = 100.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hampi AI|State")
	EHampiBotState CurrentState = EHampiBotState::Patrol;

	UFUNCTION(BlueprintPure, Category = "Hampi AI|State")
	FString GetBotStateName() const;

	UFUNCTION(BlueprintPure, Category = "Hampi AI|State")
	float GetCurrentHealth() const { return CurrentHealth; }

	UFUNCTION(BlueprintPure, Category = "Hampi AI|State")
	bool IsBotAlive() const { return CurrentHealth > 0.0f; }

	/** Applies a persona's stats. Safe to call immediately after spawning. */
	UFUNCTION(BlueprintCallable, Category = "Hampi AI|Identity")
	void SetBotPersona(EHampiBotPersona InPersona);

	/** Test-only helper so damage/death can be verified without another weapon. */
	UFUNCTION(BlueprintCallable, Category = "Hampi AI|Debug")
	void ApplyTestDamage(float Amount);

private:
	void ApplyPersonaStats();
	void ConfigureAnimation();
	void UpdateAnimation(float DeltaSeconds);
	void DetectPlayer();
	void UpdateState();
	void Move(float DeltaSeconds);
	void TryFire();
	void Die();
	FVector GetEyeLocation() const;
	FVector GetPlayerChestLocation(const AHampiSoldierCharacter* Player) const;
	bool HasLineOfSight(const AHampiSoldierCharacter* Player) const;
	void ChoosePatrolPoint();

	UPROPERTY(Transient)
	TObjectPtr<AHampiSoldierCharacter> TargetPlayer;

	UPROPERTY(Transient)
	TObjectPtr<USoundWave> BotFireSound;

	FVector SpawnLocation = FVector::ZeroVector;
	FVector PatrolTarget = FVector::ZeroVector;
	FVector LastKnownPlayerLocation = FVector::ZeroVector;
	float NextDetectionTime = 0.0f;
	float NextPatrolTime = 0.0f;
	float NextFireTime = 0.0f;
	float NextHealTime = 0.0f;
	float LastSeenTime = -1000.0f;

	float SightRadius = 3000.0f;
	float AttackRange = 1800.0f;
	float PreferredRange = 900.0f;
	float FireInterval = 0.55f;
	float AttackDamage = 8.0f;
	float PatrolRadius = 1400.0f;
	float StrafeDirection = 1.0f;
};
