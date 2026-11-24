#include "HampiSoldierCharacter.h"

#include "HampiAIBotSpawner.h"
#include "HampiDialogueDirector.h"
#include "HampiHealingItem.h"
#include "HampiLootItem.h"
#include "HampiMobileHUDWidget.h"
#include "HampiSafeZone.h"
#include "M416Weapon.h"

#include "Animation/AnimSingleNodeInstance.h"
#include "Blueprint/UserWidget.h"
#include "Animation/AnimationAsset.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/DamageType.h"
#include "GameFramework/PlayerStart.h"
#include "InputAction.h"
#include "UObject/ConstructorHelpers.h"

AHampiSoldierCharacter::AHampiSoldierCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->NavAgentProps.bCanCrouch = true;
		Movement->SetCrouchedHalfHeight(60.0f);
	}

	static ConstructorHelpers::FObjectFinder<UInputAction> FireFinder(
		TEXT("/Game/ThirdPerson/Input/Actions/IA_M416_Fire.IA_M416_Fire"));
	static ConstructorHelpers::FObjectFinder<UInputAction> AimFinder(
		TEXT("/Game/ThirdPerson/Input/Actions/IA_M416_Aim.IA_M416_Aim"));
	static ConstructorHelpers::FObjectFinder<UInputAction> ReloadFinder(
		TEXT("/Game/ThirdPerson/Input/Actions/IA_M416_Reload.IA_M416_Reload"));
	static ConstructorHelpers::FObjectFinder<UInputAction> PickupFinder(
		TEXT("/Game/ThirdPerson/Input/Actions/IA_M416_Pickup.IA_M416_Pickup"));

	if (FireFinder.Succeeded())
	{
		M416FireAction = FireFinder.Object;
	}
	if (AimFinder.Succeeded())
	{
		M416AimAction = AimFinder.Object;
	}
	if (ReloadFinder.Succeeded())
	{
		M416ReloadAction = ReloadFinder.Object;
	}
	if (PickupFinder.Succeeded())
	{
		M416PickupAction = PickupFinder.Object;
	}
}

void AHampiSoldierCharacter::ConfigureSoldierAnimation()
{
	USkeletalMeshComponent* MeshComp = GetMesh();
	if (!MeshComp || !LocomotionAsset)
	{
		return;
	}

	// The template AnimBlueprint targets the Manny skeleton. SingleNode mode lets
	// the soldier play its own imported clips without that skeleton dependency.
	MeshComp->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	MeshComp->PlayAnimation(LocomotionAsset, true);

	if (UAnimSingleNodeInstance* SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance()))
	{
		SingleNode->SetLooping(true);
		SingleNode->SetPlayRate(1.0f);
	}
}

void AHampiSoldierCharacter::ReplaceM416PickupMarker()
{
	static const FName PickupTag(TEXT("M416Pickup"));

	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Marker = *It;
		if (!Marker || Marker == this || !Marker->ActorHasTag(PickupTag))
		{
			continue;
		}

		const FVector Location = Marker->GetActorLocation();
		const FRotator Rotation = Marker->GetActorRotation();

		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AM416Weapon* Weapon = GetWorld()->SpawnActor<AM416Weapon>(
			AM416Weapon::StaticClass(), Location, Rotation, Params);
		if (Weapon)
		{
			Marker->Destroy();
		}
		return;
	}
}

void AHampiSoldierCharacter::SpawnAIBots()
{
	for (TActorIterator<AHampiAIBotSpawner> It(GetWorld()); It; ++It)
	{
		return; // Only one spawner per world.
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	GetWorld()->SpawnActor<AHampiAIBotSpawner>(
		AHampiAIBotSpawner::StaticClass(), GetActorLocation(), FRotator::ZeroRotator, Params);
}

void AHampiSoldierCharacter::SpawnSafeZone()
{
	for (TActorIterator<AHampiSafeZone> It(GetWorld()); It; ++It)
	{
		return; // Only one zone per world.
	}

	FVector CenterLocation = GetActorLocation();
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		CenterLocation = (*It)->GetActorLocation();
		break;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FVector ZoneCenter(CenterLocation.X, CenterLocation.Y, CenterLocation.Z - 250.0f);
	GetWorld()->SpawnActor<AHampiSafeZone>(
		AHampiSafeZone::StaticClass(), ZoneCenter, FRotator::ZeroRotator, Params);
}

void AHampiSoldierCharacter::SpawnHealingItems()
{
	for (TActorIterator<AHampiHealingItem> It(GetWorld()); It; ++It)
	{
		return; // Only one set per world.
	}

	FVector CenterLocation = GetActorLocation();
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		CenterLocation = (*It)->GetActorLocation();
		break;
	}

	struct FHealingSpawn
	{
		EHampiHealingItemType Type;
		float X;
		float Y;
		float Amount;
	};

	const FHealingSpawn Spawns[] = {
		{EHampiHealingItemType::Medkit, 350.0f, 0.0f, 50.0f},
		{EHampiHealingItemType::EnergyDrink, -350.0f, 180.0f, 40.0f},
		{EHampiHealingItemType::Armor, 0.0f, -420.0f, 50.0f},
	};

	for (const FHealingSpawn& Def : Spawns)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector Location(CenterLocation.X + Def.X, CenterLocation.Y + Def.Y, CenterLocation.Z);
		AHampiHealingItem* Item = GetWorld()->SpawnActor<AHampiHealingItem>(
			AHampiHealingItem::StaticClass(), Location, FRotator::ZeroRotator, Params);
		if (Item)
		{
			Item->ItemType = Def.Type;
			Item->HealAmount = Def.Amount;
		}
	}
}

void AHampiSoldierCharacter::SpawnLootItems()
{
	for (TActorIterator<AHampiLootItem> It(GetWorld()); It; ++It)
	{
		return; // Only one loot set per world.
	}

	FVector CenterLocation = GetActorLocation();
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		CenterLocation = (*It)->GetActorLocation();
		break;
	}

	struct FLootSpawn
	{
		EHampiLootType Type;
		float X;
		float Y;
		int32 Amount;
	};

	const FLootSpawn Spawns[] = {
		{EHampiLootType::Ammo556, 650.0f, 250.0f, 60},
		{EHampiLootType::Ammo556, -700.0f, -320.0f, 30},
		{EHampiLootType::Medkit, 900.0f, -450.0f, 1},
		{EHampiLootType::EnergyDrink, -900.0f, 420.0f, 2},
		{EHampiLootType::Armor, 120.0f, 780.0f, 1},
	};

	for (const FLootSpawn& Def : Spawns)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		const FVector Location(CenterLocation.X + Def.X, CenterLocation.Y + Def.Y, CenterLocation.Z);
		AHampiLootItem* Item = GetWorld()->SpawnActor<AHampiLootItem>(
			AHampiLootItem::StaticClass(), Location, FRotator::ZeroRotator, Params);
		if (Item)
		{
			Item->LootType = Def.Type;
			Item->Amount = Def.Amount;
		}
	}
}

void AHampiSoldierCharacter::SpawnDialogueDirector()
{
	for (TActorIterator<AHampiDialogueDirector> It(GetWorld()); It; ++It)
	{
		return; // Only one dialogue director per world.
	}

	FVector SpawnLocation = GetActorLocation();
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		SpawnLocation = (*It)->GetActorLocation();
		break;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	GetWorld()->SpawnActor<AHampiDialogueDirector>(
		AHampiDialogueDirector::StaticClass(), SpawnLocation, FRotator::ZeroRotator, Params);
}

void AHampiSoldierCharacter::SpawnMobileHUD()
{
	if (MobileHUDWidget)
	{
		return;
	}

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC || !PC->IsLocalController())
	{
		return;
	}

	MobileHUDWidget = CreateWidget<UHampiMobileHUDWidget>(PC, UHampiMobileHUDWidget::StaticClass());
	if (MobileHUDWidget)
	{
		MobileHUDWidget->AddToViewport(10);
	}
}

void AHampiSoldierCharacter::PlayDialogueCue(const FString& CueName)
{
	for (TActorIterator<AHampiDialogueDirector> It(GetWorld()); It; ++It)
	{
		if (*It)
		{
			(*It)->PlayDialogue(CueName);
			return;
		}
	}
}

void AHampiSoldierCharacter::BeginPlay()
{
	Super::BeginPlay();
	CurrentPlayerHealth = MaxPlayerHealth;
	CurrentPlayerShield = 0.0f;
	LastDamageTime = -1000.0f;
	HealRemaining = 0.0f;
	HealPerSecond = 0.0f;
	LastDamageSource = TEXT("None");
	ConfigureSoldierAnimation();
	ReplaceM416PickupMarker();
	SpawnAIBots();
	SpawnSafeZone();
	SpawnHealingItems();
	SpawnLootItems();
	SpawnDialogueDirector();
	SpawnMobileHUD();
	ActiveWeaponSlot = TEXT("Primary");
	Inventory.Reset();
	PrimaryWeaponSlot = TEXT("None");
	SecondaryWeaponSlot = TEXT("None");
	PistolWeaponSlot = TEXT("None");
}

bool AHampiSoldierCharacter::IsPlayerAirborne() const
{
	const UCharacterMovementComponent* Movement = GetCharacterMovement();
	return Movement && Movement->IsFalling();
}

void AHampiSoldierCharacter::MobileJump()
{
	++MobileJumpCallCount;
	if (!IsPlayerAlive())
	{
		bLastMobileJumpAllowed = false;
		return;
	}

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	bLastMobileJumpAllowed = Movement && Movement->IsMovingOnGround();
	bLastMobileJumpLaunched = false;
	LastMobileJumpLaunchZ = Movement ? Movement->JumpZVelocity : 0.0f;

	// The template pawn already binds IA_Jump to ACharacter::Jump/StopJumping.
	// Use the character movement jump implementation directly so a same-frame
	// simulated key release cannot cancel the touch tap before CheckJumpInput.
	if (Movement && Movement->DoJump(false))
	{
		bLastMobileJumpLaunched = true;
		return;
	}

	// Fallback for a character that is just leaving the ground: apply the
	// configured vertical velocity without overriding horizontal momentum.
	if (Movement)
	{
		LaunchCharacter(FVector(0.0f, 0.0f, Movement->JumpZVelocity), false, true);
		bLastMobileJumpLaunched = true;
	}
}

void AHampiSoldierCharacter::MobileStopJump()
{
	StopJumping();
}

void AHampiSoldierCharacter::TogglePlayerCrouch()
{
	if (!IsPlayerAlive())
	{
		return;
	}
	if (bIsCrouched)
	{
		UnCrouch();
	}
	else
	{
		Crouch();
	}
}

float AHampiSoldierCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
	AController* EventInstigator, AActor* DamageCauser)
{
	const float Applied = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
	if (Applied <= 0.0f || !IsPlayerAlive())
	{
		return Applied;
	}

	LastDamageTime = GetWorld()->GetTimeSeconds();
	LastDamageSource = DamageCauser ? DamageCauser->GetName() : TEXT("Unknown");
	HealRemaining = 0.0f; // Taking damage cancels the energy-drink heal.

	float Remaining = Applied;
	if (CurrentPlayerShield > 0.0f)
	{
		const float ShieldAbsorbed = FMath::Min(CurrentPlayerShield, Remaining);
		CurrentPlayerShield -= ShieldAbsorbed;
		Remaining -= ShieldAbsorbed;
	}

	if (Remaining > 0.0f)
	{
		CurrentPlayerHealth = FMath::Max(0.0f, CurrentPlayerHealth - Remaining);
	}

	if (CurrentPlayerHealth <= 0.0f)
	{
		Die(LastDamageSource);
	}
	return Applied;
}

void AHampiSoldierCharacter::Heal(float Amount)
{
	if (!IsPlayerAlive() || Amount <= 0.0f)
	{
		return;
	}
	const float PreviousHealth = CurrentPlayerHealth;
	CurrentPlayerHealth = FMath::Min(MaxPlayerHealth, CurrentPlayerHealth + Amount);
	if (CurrentPlayerHealth > PreviousHealth)
	{
		PlayDialogueCue(TEXT("Healing"));
	}
}

void AHampiSoldierCharacter::StartHealOverTime(float Amount, float Duration)
{
	if (!IsPlayerAlive() || Amount <= 0.0f || Duration <= 0.0f)
	{
		return;
	}
	HealRemaining = FMath::Min(Amount, MaxPlayerHealth - CurrentPlayerHealth);
	HealPerSecond = HealRemaining / Duration;
	if (HealRemaining > 0.0f)
	{
		PlayDialogueCue(TEXT("Healing"));
	}
}

void AHampiSoldierCharacter::AddShield(float Amount)
{
	if (!IsPlayerAlive() || Amount <= 0.0f)
	{
		return;
	}
	CurrentPlayerShield = FMath::Min(MaxPlayerShield, CurrentPlayerShield + Amount);
}

void AHampiSoldierCharacter::ApplyTestDamage(float Amount)
{
	FDamageEvent Event;
	TakeDamage(FMath::Max(0.0f, Amount), Event, nullptr, this);
}

void AHampiSoldierCharacter::Die(const FString& KillerName)
{
	CurrentPlayerHealth = 0.0f;
	CurrentPlayerShield = 0.0f;
	HealRemaining = 0.0f;
	LastDamageSource = KillerName.IsEmpty() ? TEXT("Unknown") : KillerName;
	StopM416Fire();
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->DisableMovement();
	}
}

void AHampiSoldierCharacter::Respawn()
{
	FVector SpawnLocation = GetActorLocation();
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		SpawnLocation = (*It)->GetActorLocation();
		break;
	}

	SetActorLocation(SpawnLocation, false, nullptr, ETeleportType::TeleportPhysics);
	CurrentPlayerHealth = MaxPlayerHealth;
	CurrentPlayerShield = 0.0f;
	HealRemaining = 0.0f;
	HealPerSecond = 0.0f;
	LastDamageSource = TEXT("None");
	LastDamageTime = -1000.0f;
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->SetMovementMode(MOVE_Walking);
	}
}

bool AHampiSoldierCharacter::AddInventoryItem(const FString& ItemId, int32 Amount)
{
	if (ItemId.IsEmpty() || Amount <= 0)
	{
		return false;
	}

	for (FHampiInventoryEntry& Entry : Inventory)
	{
		if (Entry.ItemId.Equals(ItemId, ESearchCase::IgnoreCase))
		{
			Entry.Quantity += Amount;
			return true;
		}
	}

	FHampiInventoryEntry NewEntry;
	NewEntry.ItemId = ItemId;
	NewEntry.Quantity = Amount;
	Inventory.Add(NewEntry);
	return true;
}

int32 AHampiSoldierCharacter::GetInventoryCount(const FString& ItemId) const
{
	for (const FHampiInventoryEntry& Entry : Inventory)
	{
		if (Entry.ItemId.Equals(ItemId, ESearchCase::IgnoreCase))
		{
			return Entry.Quantity;
		}
	}
	return 0;
}

bool AHampiSoldierCharacter::UseConsumable(const FString& ItemId)
{
	if (!IsPlayerAlive() || GetInventoryCount(ItemId) <= 0)
	{
		return false;
	}

	if (ItemId.Equals(TEXT("Medkit"), ESearchCase::IgnoreCase))
	{
		if (CurrentPlayerHealth >= MaxPlayerHealth)
		{
			return false;
		}
		Heal(50.0f);
	}
	else if (ItemId.Equals(TEXT("EnergyDrink"), ESearchCase::IgnoreCase))
	{
		if (CurrentPlayerHealth >= MaxPlayerHealth)
		{
			return false;
		}
		StartHealOverTime(40.0f, 5.0f);
	}
	else if (ItemId.Equals(TEXT("Armor"), ESearchCase::IgnoreCase))
	{
		if (CurrentPlayerShield >= MaxPlayerShield)
		{
			return false;
		}
		AddShield(50.0f);
	}
	else
	{
		return false;
	}

	for (FHampiInventoryEntry& Entry : Inventory)
	{
		if (Entry.ItemId.Equals(ItemId, ESearchCase::IgnoreCase))
		{
			Entry.Quantity = FMath::Max(0, Entry.Quantity - 1);
			break;
		}
	}
	return true;
}

FString AHampiSoldierCharacter::GetInventorySummary() const
{
	FString Result;
	for (const FHampiInventoryEntry& Entry : Inventory)
	{
		if (!Result.IsEmpty())
		{
			Result += TEXT(", ");
		}
		Result += FString::Printf(TEXT("%s x%d"), *Entry.ItemId, Entry.Quantity);
	}
	return Result.IsEmpty() ? TEXT("Empty") : Result;
}

void AHampiSoldierCharacter::SetWeaponSlot(const FString& SlotName, const FString& ItemId)
{
	if (SlotName.Equals(TEXT("Primary"), ESearchCase::IgnoreCase))
	{
		PrimaryWeaponSlot = ItemId;
	}
	else if (SlotName.Equals(TEXT("Secondary"), ESearchCase::IgnoreCase))
	{
		SecondaryWeaponSlot = ItemId;
	}
	else if (SlotName.Equals(TEXT("Pistol"), ESearchCase::IgnoreCase))
	{
		PistolWeaponSlot = ItemId;
	}
}

FString AHampiSoldierCharacter::GetWeaponSlot(const FString& SlotName) const
{
	if (SlotName.Equals(TEXT("Primary"), ESearchCase::IgnoreCase))
	{
		return PrimaryWeaponSlot;
	}
	if (SlotName.Equals(TEXT("Secondary"), ESearchCase::IgnoreCase))
	{
		return SecondaryWeaponSlot;
	}
	if (SlotName.Equals(TEXT("Pistol"), ESearchCase::IgnoreCase))
	{
		return PistolWeaponSlot;
	}
	return TEXT("InvalidSlot");
}

void AHampiSoldierCharacter::CycleWeaponSlot()
{
	static const FString Slots[] = { TEXT("Primary"), TEXT("Secondary"), TEXT("Pistol") };
	int32 CurrentIndex = 0;
	for (int32 i = 0; i < 3; ++i)
	{
		if (ActiveWeaponSlot.Equals(Slots[i], ESearchCase::IgnoreCase))
		{
			CurrentIndex = i;
			break;
		}
	}
	ActiveWeaponSlot = Slots[(CurrentIndex + 1) % 3];
	if (ActiveWeaponSlot.Equals(TEXT("Primary"), ESearchCase::IgnoreCase) && !EquippedM416)
	{
		TryPickupM416();
	}
}

void AHampiSoldierCharacter::TickHealth(float DeltaSeconds)
{
	if (!IsPlayerAlive())
	{
		return;
	}

	const float Now = GetWorld()->GetTimeSeconds();

	if (HealRemaining > 0.0f && HealPerSecond > 0.0f)
	{
		const float HealStep = FMath::Min(HealRemaining, HealPerSecond * DeltaSeconds);
		CurrentPlayerHealth = FMath::Min(MaxPlayerHealth, CurrentPlayerHealth + HealStep);
		HealRemaining -= HealStep;
		if (HealRemaining <= 0.0f)
		{
			HealRemaining = 0.0f;
			HealPerSecond = 0.0f;
		}
	}

	if (HealthRegenPerSecond > 0.0f && HealRemaining <= 0.0f &&
		Now - LastDamageTime >= HealthRegenDelay && CurrentPlayerHealth < MaxPlayerHealth)
	{
		CurrentPlayerHealth = FMath::Min(
			MaxPlayerHealth, CurrentPlayerHealth + HealthRegenPerSecond * DeltaSeconds);
	}
}

void AHampiSoldierCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	TickHealth(DeltaSeconds);

	if (!bDriveLocomotionAnimation)
	{
		return;
	}

	USkeletalMeshComponent* MeshComp = GetMesh();
	if (!MeshComp)
	{
		return;
	}

	UAnimSingleNodeInstance* SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance());
	if (!SingleNode)
	{
		ConfigureSoldierAnimation();
		SingleNode = Cast<UAnimSingleNodeInstance>(MeshComp->GetAnimInstance());
		if (!SingleNode)
		{
			return;
		}
	}

	const FVector Velocity = GetVelocity();
	const float HorizontalSpeed = FVector(Velocity.X, Velocity.Y, 0.0f).Size();
	const float BlendInput = FMath::Clamp(HorizontalSpeed, 0.0f, FMath::Max(1.0f, MaxLocomotionSpeed));
	SingleNode->SetBlendSpacePosition(FVector(BlendInput, 0.0f, 0.0f));
}

void AHampiSoldierCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EnhancedInput)
	{
		return;
	}

	if (M416FireAction)
	{
		EnhancedInput->BindAction(M416FireAction, ETriggerEvent::Started,
			this, &AHampiSoldierCharacter::StartM416Fire);
		EnhancedInput->BindAction(M416FireAction, ETriggerEvent::Completed,
			this, &AHampiSoldierCharacter::StopM416Fire);
	}
	if (M416AimAction)
	{
		EnhancedInput->BindAction(M416AimAction, ETriggerEvent::Started,
			this, &AHampiSoldierCharacter::StartM416Aim);
		EnhancedInput->BindAction(M416AimAction, ETriggerEvent::Completed,
			this, &AHampiSoldierCharacter::StopM416Aim);
	}
	if (M416ReloadAction)
	{
		EnhancedInput->BindAction(M416ReloadAction, ETriggerEvent::Started,
			this, &AHampiSoldierCharacter::ReloadM416);
	}
	if (M416PickupAction)
	{
		EnhancedInput->BindAction(M416PickupAction, ETriggerEvent::Started,
			this, &AHampiSoldierCharacter::HandlePickupInput);
	}
}

void AHampiSoldierCharacter::HandlePickupInput()
{
	TryPickupM416();
}

void AHampiSoldierCharacter::EquipM416(AM416Weapon* Weapon)
{
	if (!Weapon || Weapon->IsEquipped())
	{
		return;
	}
	if (EquippedM416 && EquippedM416 != Weapon)
	{
		return;
	}

	EquippedM416 = Weapon;
	PrimaryWeaponSlot = TEXT("M416");
	ActiveWeaponSlot = TEXT("Primary");
	PlayDialogueCue(TEXT("WeaponEquipped"));
	Weapon->EquipTo(this);
}

bool AHampiSoldierCharacter::TryPickupM416()
{
	if (EquippedM416)
	{
		return true;
	}

	AM416Weapon* Nearest = nullptr;
	float BestDistSq = FMath::Square(M416PickupRange);
	for (TActorIterator<AM416Weapon> It(GetWorld()); It; ++It)
	{
		AM416Weapon* Candidate = *It;
		if (!Candidate || Candidate->IsEquipped())
		{
			continue;
		}
		const float DistSq = FVector::DistSquared(GetActorLocation(), Candidate->GetActorLocation());
		if (DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Nearest = Candidate;
		}
	}

	if (!Nearest)
	{
		return false;
	}

	EquipM416(Nearest);
	return true;
}

void AHampiSoldierCharacter::StartM416Fire()
{
	if (EquippedM416)
	{
		EquippedM416->SetTriggerDown(true);
	}
}

void AHampiSoldierCharacter::StopM416Fire()
{
	if (EquippedM416)
	{
		EquippedM416->SetTriggerDown(false);
	}
}

void AHampiSoldierCharacter::StartM416Aim()
{
	bIsAimingM416 = true;
	if (EquippedM416)
	{
		EquippedM416->SetAiming(true);
	}

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (PC && PC->PlayerCameraManager)
	{
		if (SavedCameraFOV <= 0.0f)
		{
			SavedCameraFOV = PC->PlayerCameraManager->GetFOVAngle();
		}
		PC->PlayerCameraManager->SetFOV(AimCameraFOV);
	}
}

void AHampiSoldierCharacter::StopM416Aim()
{
	bIsAimingM416 = false;
	if (EquippedM416)
	{
		EquippedM416->SetAiming(false);
	}

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (PC && PC->PlayerCameraManager && SavedCameraFOV > 0.0f)
	{
		PC->PlayerCameraManager->SetFOV(SavedCameraFOV);
	}
}

void AHampiSoldierCharacter::ReloadM416()
{
	if (EquippedM416)
	{
		EquippedM416->Reload();
	}
}
