#include "HampiDialogueDirector.h"

#include "HampiAICharacter.h"
#include "HampiSafeZone.h"
#include "HampiSoldierCharacter.h"

#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Sound/SoundWave.h"

AHampiDialogueDirector::AHampiDialogueDirector()
{
	PrimaryActorTick.bCanEverTick = true;

	AudioComponent = CreateDefaultSubobject<UAudioComponent>(TEXT("AudioComponent"));
	RootComponent = AudioComponent;
	AudioComponent->bAutoActivate = false;
	AudioComponent->bAllowSpatialization = false;
	AudioComponent->SetVolumeMultiplier(0.75f);
}

void AHampiDialogueDirector::CacheSounds()
{
	DialogueSounds.Empty();

	struct FCueAsset
	{
		const TCHAR* Cue;
		const TCHAR* Path;
	};

	const FCueAsset Cues[] = {
		{TEXT("MatchStart"), TEXT("/Game/Audio/Dialogue/VO_MatchStart.VO_MatchStart")},
		{TEXT("WeaponEquipped"), TEXT("/Game/Audio/Dialogue/VO_WeaponEquipped.VO_WeaponEquipped")},
		{TEXT("EnemySpotted"), TEXT("/Game/Audio/Dialogue/VO_EnemySpotted.VO_EnemySpotted")},
		{TEXT("ZoneWarning"), TEXT("/Game/Audio/Dialogue/VO_ZoneWarning.VO_ZoneWarning")},
		{TEXT("LowHealth"), TEXT("/Game/Audio/Dialogue/VO_LowHealth.VO_LowHealth")},
		{TEXT("Healing"), TEXT("/Game/Audio/Dialogue/VO_Healing.VO_Healing")},
		{TEXT("Victory"), TEXT("/Game/Audio/Dialogue/VO_Victory.VO_Victory")},
		{TEXT("Defeat"), TEXT("/Game/Audio/Dialogue/VO_Defeat.VO_Defeat")},
	};

	for (const FCueAsset& Entry : Cues)
	{
		USoundWave* Sound = LoadObject<USoundWave>(nullptr, Entry.Path);
		if (Sound)
		{
			DialogueSounds.Add(Entry.Cue, Sound);
		}
	}
}

void AHampiDialogueDirector::BeginPlay()
{
	Super::BeginPlay();
	CacheSounds();
	StartTime = GetWorld()->GetTimeSeconds();
}

bool AHampiDialogueDirector::IsPlayingDialogue() const
{
	return AudioComponent && AudioComponent->IsPlaying();
}

FString AHampiDialogueDirector::GetPlayedCueHistory() const
{
	return PlayedCues.Num() > 0 ? FString::Join(PlayedCues, TEXT(",")) : TEXT("None");
}

bool AHampiDialogueDirector::IsDialogueAvailable(const FString& CueName) const
{
	return DialogueSounds.Contains(CueName);
}

bool AHampiDialogueDirector::PlayDialogue(const FString& CueName)
{
	USoundWave* Sound = DialogueSounds.FindRef(CueName);
	if (!Sound || !AudioComponent)
	{
		return false;
	}

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	if (const float* Last = LastPlayedTime.Find(CueName))
	{
		if (Now - *Last < CueCooldown)
		{
			return false;
		}
	}

	LastPlayedTime.Add(CueName, Now);
	LastCue = CueName;
	PlayedCues.Add(CueName);
	AudioComponent->SetSound(Sound);
	AudioComponent->Play();
	UE_LOG(LogTemp, Display, TEXT("HampiDialogue: %s"), *CueName);
	return true;
}

void AHampiDialogueDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Now = GetWorld()->GetTimeSeconds();
	if (!bMatchStartPlayed && Now - StartTime >= 1.5f)
	{
		bMatchStartPlayed = PlayDialogue(TEXT("MatchStart"));
	}

	AHampiSoldierCharacter* Player = nullptr;
	for (TActorIterator<AHampiSoldierCharacter> It(GetWorld()); It; ++It)
	{
		Player = *It;
		break;
	}
	if (!Player)
	{
		return;
	}

	if (!bLowHealthPlayed && Player->IsPlayerAlive() &&
		Player->GetHealthFraction() <= 0.35f)
	{
		bLowHealthPlayed = PlayDialogue(TEXT("LowHealth"));
	}

	if (!bDefeatPlayed && !Player->IsPlayerAlive())
	{
		bDefeatPlayed = PlayDialogue(TEXT("Defeat"));
	}

	if (!bZoneWarningPlayed)
	{
		for (TActorIterator<AHampiSafeZone> It(GetWorld()); It; ++It)
		{
			if (*It && (*It)->GetPhase() > 0)
			{
				bZoneWarningPlayed = PlayDialogue(TEXT("ZoneWarning"));
				break;
			}
		}
	}

	if (!bEnemySpottedPlayed && Player->IsPlayerAlive())
	{
		const FVector PlayerLocation = Player->GetActorLocation();
		for (TActorIterator<AHampiAICharacter> It(GetWorld()); It; ++It)
		{
			AHampiAICharacter* Bot = *It;
			if (Bot && Bot->IsBotAlive() &&
				FVector::DistSquared(Bot->GetActorLocation(), PlayerLocation) <= FMath::Square(2500.0f))
			{
				bEnemySpottedPlayed = PlayDialogue(TEXT("EnemySpotted"));
				break;
			}
		}
	}

	if (!bVictoryPlayed && Player->IsPlayerAlive())
	{
		int32 AliveBots = 0;
		int32 TotalBots = 0;
		for (TActorIterator<AHampiAICharacter> It(GetWorld()); It; ++It)
		{
			++TotalBots;
			if (*It && (*It)->IsBotAlive())
			{
				++AliveBots;
			}
		}
		if (TotalBots >= 5 && AliveBots == 0)
		{
			bVictoryPlayed = PlayDialogue(TEXT("Victory"));
		}
	}
}
