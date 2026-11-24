#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HampiDialogueDirector.generated.h"

class UAudioComponent;
class USoundWave;

/**
 * Plays North Karnataka Kannada battle dialogue. Cues can be triggered by
 * gameplay code with PlayDialogue(); the director also watches simple state
 * (nearby bots, zone phase, low health, victory) for automatic barks.
 */
UCLASS()
class BATTLEGROUND_API AHampiDialogueDirector : public AActor
{
	GENERATED_BODY()

public:
	AHampiDialogueDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Plays a cue if it exists and is not on cooldown. Returns true when played. */
	UFUNCTION(BlueprintCallable, Category = "Hampi Dialogue")
	bool PlayDialogue(const FString& CueName);

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	bool IsDialogueAvailable(const FString& CueName) const;

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	FString GetLastCue() const { return LastCue; }

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	int32 GetDialogueCount() const { return DialogueSounds.Num(); }

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	bool HasPlayedCue(const FString& CueName) const { return PlayedCues.Contains(CueName); }

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	int32 GetPlayedCueCount() const { return PlayedCues.Num(); }

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	FString GetPlayedCueHistory() const;

	UFUNCTION(BlueprintPure, Category = "Hampi Dialogue")
	bool IsPlayingDialogue() const;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hampi Dialogue", meta = (ClampMin = "0.0"))
	float CueCooldown = 6.0f;

private:
	void CacheSounds();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UAudioComponent> AudioComponent;

	UPROPERTY(Transient)
	TMap<FString, TObjectPtr<USoundWave>> DialogueSounds;

	TMap<FString, float> LastPlayedTime;
	TArray<FString> PlayedCues;
	FString LastCue = TEXT("None");

	bool bMatchStartPlayed = false;
	bool bZoneWarningPlayed = false;
	bool bLowHealthPlayed = false;
	bool bEnemySpottedPlayed = false;
	bool bVictoryPlayed = false;
	bool bDefeatPlayed = false;
	float StartTime = 0.0f;
};
