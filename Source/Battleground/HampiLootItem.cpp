#include "HampiLootItem.h"

#include "HampiSoldierCharacter.h"

#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

AHampiLootItem::AHampiLootItem()
{
	PrimaryActorTick.bCanEverTick = true;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);

	Marker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Marker"));
	Marker->SetupAttachment(Mesh);
	Marker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Marker->SetCastShadow(false);
	Marker->SetRelativeLocation(FVector(0.0f, 0.0f, 180.0f));
	Marker->SetRelativeScale3D(FVector(0.06f, 0.06f, 3.2f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(
		TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CubeFinder.Succeeded())
	{
		Mesh->SetStaticMesh(CubeFinder.Object);
		Mesh->SetRelativeScale3D(FVector(0.5f, 0.5f, 0.5f));
	}
	if (CylinderFinder.Succeeded())
	{
		Marker->SetStaticMesh(CylinderFinder.Object);
	}
}

FString AHampiLootItem::GetLootTypeId() const
{
	switch (LootType)
	{
	case EHampiLootType::Ammo556: return TEXT("Ammo556");
	case EHampiLootType::Medkit: return TEXT("Medkit");
	case EHampiLootType::EnergyDrink: return TEXT("EnergyDrink");
	case EHampiLootType::Armor: return TEXT("Armor");
	default: return TEXT("Unknown");
	}
}

FString AHampiLootItem::GetLootDisplayName() const
{
	switch (LootType)
	{
	case EHampiLootType::Ammo556: return TEXT("5.56mm Ammo");
	case EHampiLootType::Medkit: return TEXT("Medkit");
	case EHampiLootType::EnergyDrink: return TEXT("Energy Drink");
	case EHampiLootType::Armor: return TEXT("Armor Plate");
	default: return TEXT("Unknown");
	}
}

void AHampiLootItem::BeginPlay()
{
	Super::BeginPlay();

	const TCHAR* MaterialPath = nullptr;
	switch (LootType)
	{
	case EHampiLootType::Ammo556:
		MaterialPath = TEXT("/Game/Environment/Loot/M_LootAmmo.M_LootAmmo");
		break;
	case EHampiLootType::Medkit:
		MaterialPath = TEXT("/Game/Environment/Health/M_Medkit.M_Medkit");
		break;
	case EHampiLootType::EnergyDrink:
		MaterialPath = TEXT("/Game/Environment/Health/M_EnergyDrink.M_EnergyDrink");
		break;
	case EHampiLootType::Armor:
		MaterialPath = TEXT("/Game/Environment/Health/M_Armor.M_Armor");
		break;
	default:
		break;
	}

	if (MaterialPath)
	{
		UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, MaterialPath);
		if (Material)
		{
			Mesh->SetMaterial(0, Material);
			Marker->SetMaterial(0, Material);
		}
	}
}

void AHampiLootItem::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bAvailable)
	{
		return;
	}

	AddActorLocalRotation(FRotator(0.0f, 40.0f * DeltaSeconds, 0.0f));
	Marker->SetRelativeRotation(FRotator(0.0f, -80.0f * DeltaSeconds, 0.0f));
	TryPickup();
}

void AHampiLootItem::TryPickup()
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

		Player->AddInventoryItem(GetLootTypeId(), Amount);
		bAvailable = false;
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
		SetLifeSpan(0.25f);
		return;
	}
}
