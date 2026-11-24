#include "HampiHealingItem.h"

#include "HampiSoldierCharacter.h"

#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AHampiHealingItem::AHampiHealingItem()
{
	PrimaryActorTick.bCanEverTick = true;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(
		TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		Mesh->SetStaticMesh(CubeFinder.Object);
		Mesh->SetRelativeScale3D(FVector(0.45f, 0.45f, 0.45f));
	}
}

FString AHampiHealingItem::GetItemTypeName() const
{
	switch (ItemType)
	{
	case EHampiHealingItemType::Medkit: return TEXT("Medkit");
	case EHampiHealingItemType::EnergyDrink: return TEXT("EnergyDrink");
	case EHampiHealingItemType::Armor: return TEXT("Armor");
	default: return TEXT("Unknown");
	}
}

void AHampiHealingItem::BeginPlay()
{
	Super::BeginPlay();

	const TCHAR* MaterialPath = nullptr;
	switch (ItemType)
	{
	case EHampiHealingItemType::Medkit:
		MaterialPath = TEXT("/Game/Environment/Health/M_Medkit.M_Medkit");
		break;
	case EHampiHealingItemType::EnergyDrink:
		MaterialPath = TEXT("/Game/Environment/Health/M_EnergyDrink.M_EnergyDrink");
		break;
	case EHampiHealingItemType::Armor:
		MaterialPath = TEXT("/Game/Environment/Health/M_Armor.M_Armor");
		break;
	default:
		break;
	}

	if (MaterialPath && Mesh)
	{
		UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, MaterialPath);
		if (Material)
		{
			Mesh->SetMaterial(0, Material);
		}
	}
}

void AHampiHealingItem::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bAvailable)
	{
		return;
	}

	// Slow spin keeps the pickup readable without any particle cost.
	AddActorLocalRotation(FRotator(0.0f, 55.0f * DeltaSeconds, 0.0f));
	TryPickup();
}

void AHampiHealingItem::TryPickup()
{
	const FVector Location = GetActorLocation();
	for (TActorIterator<AHampiSoldierCharacter> It(GetWorld()); It; ++It)
	{
		AHampiSoldierCharacter* Player = *It;
		if (!Player || !Player->IsPlayerAlive())
		{
			continue;
		}

		const FVector Delta = Player->GetActorLocation() - Location;
		if (FVector(Delta.X, Delta.Y, 0.0f).Size() > PickupRadius)
		{
			continue;
		}

		switch (ItemType)
		{
		case EHampiHealingItemType::Medkit:
			Player->Heal(HealAmount);
			break;
		case EHampiHealingItemType::EnergyDrink:
			Player->StartHealOverTime(HealAmount, 5.0f);
			break;
		case EHampiHealingItemType::Armor:
			Player->AddShield(HealAmount);
			break;
		default:
			break;
		}

		bAvailable = false;
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
		SetLifeSpan(0.25f);
		return;
	}
}
