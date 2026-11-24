#include "HampiMobileHUDWidget.h"

#include "HampiAICharacter.h"
#include "HampiLootItem.h"
#include "HampiSafeZone.h"
#include "HampiSoldierCharacter.h"
#include "M416Weapon.h"

#include "Blueprint/WidgetTree.h"
#include "EngineUtils.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "Input/Events.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"

namespace HampiHUD
{
	static const float JoystickBaseSize = 130.0f;
	static const float JoystickKnobSize = 52.0f;
	static const float JoystickRadius = 58.0f;
	static const float RadarRadiusPx = 66.0f;
	static const float RadarRangeCm = 6000.0f;
}

UHampiMobileHUDWidget::UHampiMobileHUDWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void UHampiMobileHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();

	ViewportSize = GetCachedGeometry().GetLocalSize();
	if (ViewportSize.X < 2.0f || ViewportSize.Y < 2.0f)
	{
		ViewportSize = FVector2D(800.0f, 450.0f);
	}

	SetIsFocusable(true);
	SetVisibility(ESlateVisibility::Visible);
	BuildLayout();
	UpdateHUD();
}

void UHampiMobileHUDWidget::NativeDestruct()
{
	Buttons.Empty();
	bLayoutBuilt = false;
	Super::NativeDestruct();
}

FReply UHampiMobileHUDWidget::NativeOnTouchStarted(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent)
{
	if (!bLayoutBuilt)
	{
		return FReply::Unhandled();
	}

	const FVector2D Local = MyGeometry.AbsoluteToLocal(InTouchEvent.GetScreenSpacePosition());
	const int32 PointerIndex = InTouchEvent.GetPointerIndex();
	if (Local.X <= ViewportSize.X * 0.5f && !bMoveTouchActive)
	{
		bMoveTouchActive = true;
		MovePointerIndex = PointerIndex;
		MoveTouchStart = Local;
		MoveTouchCurrent = Local;
		SetJoystickCenter(Local);
		return FReply::Handled();
	}
	if (!bCameraTouchActive)
	{
		bCameraTouchActive = true;
		CameraPointerIndex = PointerIndex;
		CameraTouchLast = Local;
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FReply UHampiMobileHUDWidget::NativeOnTouchMoved(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent)
{
	if (!bLayoutBuilt)
	{
		return FReply::Unhandled();
	}

	const FVector2D Local = MyGeometry.AbsoluteToLocal(InTouchEvent.GetScreenSpacePosition());
	const int32 PointerIndex = InTouchEvent.GetPointerIndex();
	if (bMoveTouchActive && PointerIndex == MovePointerIndex)
	{
		MoveTouchCurrent = Local;
		const FVector2D Delta = (Local - MoveTouchStart) / HampiHUD::JoystickRadius;
		MoveX = FMath::Clamp(Delta.X, -1.0f, 1.0f);
		MoveY = FMath::Clamp(-Delta.Y, -1.0f, 1.0f);
		UpdateJoystickVisual();
		return FReply::Handled();
	}
	if (bCameraTouchActive && PointerIndex == CameraPointerIndex)
	{
		ApplyCameraDelta(Local.X - CameraTouchLast.X, Local.Y - CameraTouchLast.Y);
		CameraTouchLast = Local;
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FReply UHampiMobileHUDWidget::NativeOnTouchEnded(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent)
{
	const int32 PointerIndex = InTouchEvent.GetPointerIndex();
	if (bMoveTouchActive && PointerIndex == MovePointerIndex)
	{
		bMoveTouchActive = false;
		MovePointerIndex = -1;
		MoveX = 0.0f;
		MoveY = 0.0f;
		UpdateJoystickVisual();
		return FReply::Handled();
	}
	if (bCameraTouchActive && PointerIndex == CameraPointerIndex)
	{
		bCameraTouchActive = false;
		CameraPointerIndex = -1;
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FReply UHampiMobileHUDWidget::NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (!bLayoutBuilt)
	{
		return FReply::Unhandled();
	}

	const FVector2D Local = MyGeometry.AbsoluteToLocal(MouseEvent.GetScreenSpacePosition());
	if (MouseEvent.GetEffectingButton() == EKeys::RightMouseButton || Local.X > ViewportSize.X * 0.5f)
	{
		bCameraTouchActive = true;
		CameraPointerIndex = MouseEvent.GetPointerIndex();
		CameraTouchLast = Local;
		return FReply::Handled();
	}

	bMoveTouchActive = true;
	MovePointerIndex = MouseEvent.GetPointerIndex();
	MoveTouchStart = Local;
	MoveTouchCurrent = Local;
	SetJoystickCenter(Local);
	return FReply::Handled();
}

FReply UHampiMobileHUDWidget::NativeOnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	return NativeOnTouchMoved(MyGeometry, MouseEvent);
}

FReply UHampiMobileHUDWidget::NativeOnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	return NativeOnTouchEnded(MyGeometry, MouseEvent);
}

void UHampiMobileHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const FVector2D CurrentSize = MyGeometry.GetLocalSize();
	if (CurrentSize.X > 2.0f && CurrentSize.Y > 2.0f)
	{
		ViewportSize = CurrentSize;
	}

	ApplyMovementInput();
	UpdateHUD();
}

void UHampiMobileHUDWidget::BuildLayout()
{
	if (bLayoutBuilt || !WidgetTree)
	{
		return;
	}

	WhiteTexture = LoadObject<UTexture2D>(nullptr,
		TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
	JoystickCenter = FVector2D(110.0f, ViewportSize.Y - 110.0f);

	RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("HampiHUDCanvas"));
	WidgetTree->RootWidget = RootCanvas;
	RootCanvas->SetVisibility(ESlateVisibility::Visible);

	// Right-side look area. It is visual only; touches are handled by this widget.
	CreateColorImage(TEXT("LookZone"), FLinearColor(0.1f, 0.3f, 0.55f, 0.08f),
		FAnchors(1.0f, 0.0f, 1.0f, 1.0f), FVector2D(-215.0f, 0.0f), FVector2D(215.0f, 0.0f));
	CreateText(TEXT("LookHint"), TEXT("SWIPE / LOOK"),
		FAnchors(1.0f, 0.0f, 1.0f, 0.0f), FVector2D(-205.0f, 196.0f), FVector2D(190.0f, 20.0f), 11);

	// Floating movement joystick.
	MoveJoystickBase = CreateColorImage(TEXT("MoveJoystickBase"), FLinearColor(0.6f, 0.8f, 1.0f, 0.22f),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(45.0f, ViewportSize.Y - 175.0f),
		FVector2D(HampiHUD::JoystickBaseSize, HampiHUD::JoystickBaseSize));
	MoveJoystickBaseSlot = Cast<UCanvasPanelSlot>(MoveJoystickBase->Slot);
	MoveJoystickKnob = CreateColorImage(TEXT("MoveJoystickKnob"), FLinearColor(1.0f, 1.0f, 1.0f, 0.65f),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(84.0f, ViewportSize.Y - 136.0f),
		FVector2D(HampiHUD::JoystickKnobSize, HampiHUD::JoystickKnobSize));
	MoveJoystickKnobSlot = Cast<UCanvasPanelSlot>(MoveJoystickKnob->Slot);

	// Health and armor panel.
	CreateColorImage(TEXT("HealthPanel"), FLinearColor(0.0f, 0.0f, 0.0f, 0.55f),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(16.0f, 16.0f), FVector2D(250.0f, 68.0f));
	StatusText = CreateText(TEXT("StatusText"), TEXT("HAMPI BATTLEGROUND"),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(24.0f, 20.0f), FVector2D(230.0f, 20.0f), 12);

	HealthBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("HealthBar"));
	PlaceWidget(HealthBar, FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(24.0f, 43.0f), FVector2D(234.0f, 14.0f));
	FProgressBarStyle HealthStyle;
	HealthStyle.BackgroundImage = MakeColorBrush(FLinearColor(0.12f, 0.12f, 0.12f, 0.9f));
	HealthStyle.FillImage = MakeColorBrush(FLinearColor(0.25f, 0.9f, 0.35f, 1.0f));
	HealthBar->SetWidgetStyle(HealthStyle);
	HealthBar->SetVisibility(ESlateVisibility::HitTestInvisible);
	HealthText = CreateText(TEXT("HealthText"), TEXT("HP 100/100"),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(128.0f, 40.0f), FVector2D(126.0f, 18.0f), 10);

	ShieldBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ShieldBar"));
	PlaceWidget(ShieldBar, FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(24.0f, 64.0f), FVector2D(234.0f, 10.0f));
	FProgressBarStyle ShieldStyle;
	ShieldStyle.BackgroundImage = MakeColorBrush(FLinearColor(0.12f, 0.12f, 0.12f, 0.9f));
	ShieldStyle.FillImage = MakeColorBrush(FLinearColor(0.2f, 0.7f, 1.0f, 1.0f));
	ShieldBar->SetWidgetStyle(ShieldStyle);
	ShieldBar->SetVisibility(ESlateVisibility::HitTestInvisible);
	ShieldText = CreateText(TEXT("ShieldText"), TEXT("ARMOR 0/50"),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(128.0f, 61.0f), FVector2D(126.0f, 18.0f), 10);

	// Compass tape.
	CreateColorImage(TEXT("CompassPanel"), FLinearColor(0.0f, 0.0f, 0.0f, 0.55f),
		FAnchors(0.5f, 0.0f, 0.5f, 0.0f), FVector2D(-210.0f, 16.0f), FVector2D(420.0f, 34.0f));
	for (int32 i = 0; i < 5; ++i)
	{
		CompassTicks.Add(CreateText(FName(*FString::Printf(TEXT("CompassTick%d"), i)), TEXT("N"),
			FAnchors(0.5f, 0.0f, 0.5f, 0.0f),
			FVector2D(-180.0f + i * 90.0f, 21.0f), FVector2D(90.0f, 24.0f), i == 2 ? 13 : 11));
	}

	// Radar/minimap with player, five enemy dots and a zone-ring approximation.
	UImage* RadarOuter = CreateColorImage(TEXT("RadarOuter"), FLinearColor(0.2f, 0.8f, 1.0f, 0.5f),
		FAnchors(1.0f, 0.0f, 1.0f, 0.0f), FVector2D(-200.0f, 16.0f), FVector2D(170.0f, 170.0f));
	RadarOuterSlot = Cast<UCanvasPanelSlot>(RadarOuter->Slot);
	CreateColorImage(TEXT("RadarInner"), FLinearColor(0.0f, 0.05f, 0.08f, 0.88f),
		FAnchors(1.0f, 0.0f, 1.0f, 0.0f), FVector2D(-196.0f, 20.0f), FVector2D(162.0f, 162.0f));
	RadarPlayerDot = CreateColorImage(TEXT("RadarPlayerDot"), FLinearColor(0.3f, 1.0f, 0.4f, 1.0f),
		FAnchors(0.0f, 0.0f, 0.0f, 0.0f), FVector2D(0.0f, 0.0f), FVector2D(8.0f, 8.0f));
	RadarPlayerDotSlot = Cast<UCanvasPanelSlot>(RadarPlayerDot->Slot);
	for (int32 i = 0; i < 5; ++i)
	{
		UImage* Dot = CreateColorImage(FName(*FString::Printf(TEXT("RadarBot%d"), i)),
			FLinearColor(1.0f, 0.2f, 0.2f, 1.0f), FAnchors(0.0f, 0.0f, 0.0f, 0.0f),
			FVector2D(0.0f, 0.0f), FVector2D(7.0f, 7.0f));
		RadarDots.Add(Dot);
		RadarDotSlots.Add(Cast<UCanvasPanelSlot>(Dot->Slot));
	}
	for (int32 i = 0; i < 12; ++i)
	{
		UImage* Segment = CreateColorImage(FName(*FString::Printf(TEXT("ZoneRing%d"), i)),
			FLinearColor(0.3f, 0.9f, 1.0f, 0.75f), FAnchors(0.0f, 0.0f, 0.0f, 0.0f),
			FVector2D(0.0f, 0.0f), FVector2D(5.0f, 5.0f));
		ZoneRingSegments.Add(Segment);
		ZoneRingSlots.Add(Cast<UCanvasPanelSlot>(Segment->Slot));
	}

	// Prompts and ammo.
	PromptTextWidget = CreateText(TEXT("PromptText"), TEXT("FIND M416 AND LOOT"),
		FAnchors(0.5f, 1.0f, 0.5f, 1.0f), FVector2D(-260.0f, -58.0f), FVector2D(520.0f, 28.0f), 13);
	PromptTextWidget->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.85f, 0.25f, 1.0f)));
	AmmoTextWidget = CreateText(TEXT("AmmoText"), TEXT("NO WEAPON"),
		FAnchors(0.5f, 1.0f, 0.5f, 1.0f), FVector2D(-180.0f, -105.0f), FVector2D(360.0f, 32.0f), 17);

	// Touch action buttons.
	Buttons.Add(TEXT("FIRE"), CreateButton(TEXT("FireButton"), TEXT("FIRE"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-20.0f, -20.0f), FVector2D(100.0f, 100.0f)));
	Buttons.Add(TEXT("ADS"), CreateButton(TEXT("AdsButton"), TEXT("ADS"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-135.0f, -20.0f), FVector2D(100.0f, 80.0f)));
	Buttons.Add(TEXT("SWAP"), CreateButton(TEXT("SwapButton"), TEXT("SWAP"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-250.0f, -20.0f), FVector2D(100.0f, 60.0f)));
	Buttons.Add(TEXT("RELOAD"), CreateButton(TEXT("ReloadButton"), TEXT("RELOAD"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-20.0f, -135.0f), FVector2D(100.0f, 60.0f)));
	Buttons.Add(TEXT("JUMP"), CreateButton(TEXT("JumpButton"), TEXT("JUMP"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-135.0f, -100.0f), FVector2D(100.0f, 60.0f)));
	Buttons.Add(TEXT("CROUCH"), CreateButton(TEXT("CrouchButton"), TEXT("CROUCH"),
		FAnchors(1.0f, 1.0f, 1.0f, 1.0f), FVector2D(-250.0f, -100.0f), FVector2D(100.0f, 60.0f)));

	Buttons[TEXT("FIRE")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleFirePressed);
	Buttons[TEXT("FIRE")]->OnReleased.AddDynamic(this, &UHampiMobileHUDWidget::HandleFireReleased);
	Buttons[TEXT("ADS")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleAimPressed);
	Buttons[TEXT("ADS")]->OnReleased.AddDynamic(this, &UHampiMobileHUDWidget::HandleAimReleased);
	Buttons[TEXT("JUMP")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleJumpPressed);
	Buttons[TEXT("JUMP")]->OnReleased.AddDynamic(this, &UHampiMobileHUDWidget::HandleJumpReleased);
	Buttons[TEXT("CROUCH")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleCrouchPressed);
	Buttons[TEXT("RELOAD")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleReloadPressed);
	Buttons[TEXT("SWAP")]->OnPressed.AddDynamic(this, &UHampiMobileHUDWidget::HandleSwapPressed);

	for (const TPair<FString, UButton*>& Pair : Buttons)
	{
		ButtonPressStates.Add(Pair.Key, false);
		ButtonPressCounts.Add(Pair.Key, 0);
	}

	UpdateJoystickVisual();
	bLayoutBuilt = true;
}

UCanvasPanelSlot* UHampiMobileHUDWidget::PlaceWidget(UWidget* Widget, FAnchors Anchors,
	FVector2D Position, FVector2D Size, FVector2D Alignment)
{
	if (!RootCanvas || !Widget)
	{
		return nullptr;
	}
	RootCanvas->AddChild(Widget);
	UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Widget->Slot);
	if (!CanvasSlot)
	{
		return nullptr;
	}
	CanvasSlot->SetAnchors(Anchors);
	CanvasSlot->SetPosition(Position);
	CanvasSlot->SetSize(Size);
	CanvasSlot->SetAlignment(Alignment);
	CanvasSlot->SetAutoSize(false);
	return CanvasSlot;
}

UImage* UHampiMobileHUDWidget::CreateColorImage(const FName& Name, const FLinearColor& Color,
	FAnchors Anchors, FVector2D Position, FVector2D Size, bool bHitTestInvisible)
{
	UImage* Image = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), Name);
	Image->SetBrush(MakeColorBrush(Color));
	PlaceWidget(Image, Anchors, Position, Size);
	Image->SetVisibility(bHitTestInvisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Visible);
	return Image;
}

UTextBlock* UHampiMobileHUDWidget::CreateText(const FName& Name, const FString& Text,
	FAnchors Anchors, FVector2D Position, FVector2D Size, int32 FontSize, bool bHitTestInvisible)
{
	UTextBlock* TextWidget = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
	TextWidget->SetText(FText::FromString(Text));
	TextWidget->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), FontSize));
	TextWidget->SetJustification(ETextJustify::Center);
	TextWidget->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 1.0f, 1.0f, 1.0f)));
	TextWidget->SetShadowOffset(FVector2D(1.0f, 1.0f));
	TextWidget->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.85f));
	PlaceWidget(TextWidget, Anchors, Position, Size);
	TextWidget->SetVisibility(bHitTestInvisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Visible);
	return TextWidget;
}

UButton* UHampiMobileHUDWidget::CreateButton(const FName& Name, const FString& Label,
	FAnchors Anchors, FVector2D Position, FVector2D Size)
{
	UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
	Button->SetBackgroundColor(FLinearColor(0.06f, 0.22f, 0.32f, 0.82f));
	UTextBlock* LabelWidget = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),
		FName(*FString::Printf(TEXT("%sLabel"), *Name.ToString())));
	LabelWidget->SetText(FText::FromString(Label));
	LabelWidget->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 13));
	LabelWidget->SetJustification(ETextJustify::Center);
	LabelWidget->SetColorAndOpacity(FSlateColor(FLinearColor(0.9f, 1.0f, 1.0f, 1.0f)));
	LabelWidget->SetVisibility(ESlateVisibility::HitTestInvisible);
	Button->AddChild(LabelWidget);
	PlaceWidget(Button, Anchors, Position, Size, FVector2D(1.0f, 1.0f));
	Button->SetVisibility(ESlateVisibility::Visible);
	return Button;
}

FSlateBrush UHampiMobileHUDWidget::MakeColorBrush(const FLinearColor& Color) const
{
	FSlateBrush Brush;
	Brush.DrawAs = ESlateBrushDrawType::Image;
	Brush.SetResourceObject(WhiteTexture);
	Brush.ImageSize = FVector2D(32.0f, 32.0f);
	Brush.TintColor = FSlateColor(Color);
	return Brush;
}

AHampiSoldierCharacter* UHampiMobileHUDWidget::GetSoldier() const
{
	return Cast<AHampiSoldierCharacter>(UGameplayStatics::GetPlayerCharacter(GetWorld(), 0));
}

void UHampiMobileHUDWidget::ApplyMovementInput()
{
	AHampiSoldierCharacter* Soldier = GetSoldier();
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!Soldier || !PC || !Soldier->IsPlayerAlive())
	{
		return;
	}
	if (FMath::Square(MoveX) + FMath::Square(MoveY) <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	const FRotator ControlRotation = PC->GetControlRotation();
	const FRotator YawRotation(0.0f, ControlRotation.Yaw, 0.0f);
	const FVector Forward = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
	Soldier->AddMovementInput(Forward, MoveY);
	Soldier->AddMovementInput(Right, MoveX);
}

void UHampiMobileHUDWidget::ApplyCameraDelta(float DeltaX, float DeltaY)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || (FMath::IsNearlyZero(DeltaX) && FMath::IsNearlyZero(DeltaY)))
	{
		return;
	}

	const float YawStep = DeltaX * MobileLookSensitivity;
	const float PitchStep = -DeltaY * MobileLookSensitivity;
	PC->AddYawInput(YawStep);
	PC->AddPitchInput(PitchStep);
	TotalCameraYawDelta += YawStep;
	TotalCameraPitchDelta += PitchStep;
}

void UHampiMobileHUDWidget::SetJoystickCenter(FVector2D LocalCenter)
{
	JoystickCenter = LocalCenter;
	if (MoveJoystickBaseSlot)
	{
		MoveJoystickBaseSlot->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f));
		MoveJoystickBaseSlot->SetPosition(FVector2D(
			LocalCenter.X - HampiHUD::JoystickBaseSize * 0.5f,
			LocalCenter.Y - HampiHUD::JoystickBaseSize * 0.5f));
	}
	UpdateJoystickVisual();
}

void UHampiMobileHUDWidget::UpdateJoystickVisual()
{
	if (!MoveJoystickKnobSlot)
	{
		return;
	}
	const FVector2D Offset(MoveX * HampiHUD::JoystickRadius, -MoveY * HampiHUD::JoystickRadius);
	MoveJoystickKnobSlot->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f));
	MoveJoystickKnobSlot->SetPosition(FVector2D(
		JoystickCenter.X + Offset.X - HampiHUD::JoystickKnobSize * 0.5f,
		JoystickCenter.Y + Offset.Y - HampiHUD::JoystickKnobSize * 0.5f));
}

FVector2D UHampiMobileHUDWidget::LocalFromNorm(float XNorm, float YNorm) const
{
	return FVector2D(FMath::Clamp(XNorm, 0.0f, 1.0f) * ViewportSize.X,
		FMath::Clamp(YNorm, 0.0f, 1.0f) * ViewportSize.Y);
}

FVector2D UHampiMobileHUDWidget::AnchorCenterLocal(UCanvasPanelSlot* CanvasSlot) const
{
	if (!CanvasSlot)
	{
		return FVector2D(ViewportSize.X * 0.5f, ViewportSize.Y * 0.5f);
	}
	const FAnchors Anchors = CanvasSlot->GetAnchors();
	const FVector2D Position = CanvasSlot->GetPosition();
	const FVector2D Size = CanvasSlot->GetSize();
	const FVector2D TopLeft(Anchors.Minimum.X * ViewportSize.X + Position.X,
		Anchors.Minimum.Y * ViewportSize.Y + Position.Y);
	const FVector2D BottomRight(Anchors.Maximum.X * ViewportSize.X + Position.X + Size.X,
		Anchors.Maximum.Y * ViewportSize.Y + Position.Y + Size.Y);
	return (TopLeft + BottomRight) * 0.5f;
}

FString UHampiMobileHUDWidget::CardinalFromYaw(float YawDegrees)
{
	float Yaw = FRotator::NormalizeAxis(YawDegrees);
	if (Yaw < 0.0f)
	{
		Yaw += 360.0f;
	}
	static const TCHAR* Names[] = { TEXT("N"), TEXT("NE"), TEXT("E"), TEXT("SE"),
		TEXT("S"), TEXT("SW"), TEXT("W"), TEXT("NW") };
	const int32 Index = FMath::RoundToInt(Yaw / 45.0f) % 8;
	return FString(Names[Index]);
}

void UHampiMobileHUDWidget::UpdateHUD()
{
	AHampiSoldierCharacter* Soldier = GetSoldier();
	if (!Soldier)
	{
		return;
	}

	if (HealthBar)
	{
		HealthBar->SetPercent(FMath::Clamp(Soldier->GetHealthFraction(), 0.0f, 1.0f));
	}
	if (ShieldBar)
	{
		const float ShieldFraction = Soldier->GetMaxPlayerShield() > 0.0f
			? Soldier->GetCurrentPlayerShield() / Soldier->GetMaxPlayerShield() : 0.0f;
		ShieldBar->SetPercent(FMath::Clamp(ShieldFraction, 0.0f, 1.0f));
	}
	if (HealthText)
	{
		HealthText->SetText(FText::FromString(FString::Printf(TEXT("HP %d/%d"),
			FMath::CeilToInt(Soldier->GetCurrentPlayerHealth()),
			FMath::CeilToInt(Soldier->GetMaxPlayerHealth()))));
	}
	if (ShieldText)
	{
		ShieldText->SetText(FText::FromString(FString::Printf(TEXT("ARMOR %d/%d"),
			FMath::CeilToInt(Soldier->GetCurrentPlayerShield()),
			FMath::CeilToInt(Soldier->GetMaxPlayerShield()))));
	}

	AM416Weapon* Weapon = Soldier->EquippedM416;
	AmmoText = Weapon
		? FString::Printf(TEXT("M416  %d / %d%s"), Weapon->GetCurrentAmmo(), Weapon->GetReserveAmmo(),
			Weapon->IsReloading() ? TEXT("  RELOADING") : TEXT(""))
		: FString(TEXT("NO WEAPON - FIND M416"));
	if (AmmoTextWidget)
	{
		AmmoTextWidget->SetText(FText::FromString(AmmoText));
	}

	if (!Weapon)
	{
		AM416Weapon* NearestWeapon = nullptr;
		float BestDistSq = FMath::Square(Soldier->M416PickupRange * 1.3f);
		for (TActorIterator<AM416Weapon> It(GetWorld()); It; ++It)
		{
			const float DistSq = FVector::DistSquared(Soldier->GetActorLocation(), (*It)->GetActorLocation());
			if (!(*It)->IsEquipped() && DistSq < BestDistSq)
			{
				BestDistSq = DistSq;
				NearestWeapon = *It;
			}
		}
		if (NearestWeapon)
		{
			PromptText = TEXT("M416 NEARBY - PRESS F OR TOUCH TO PICK UP");
		}
		else
		{
			AHampiLootItem* NearestLoot = nullptr;
			float BestLootDistSq = FMath::Square(450.0f);
			for (TActorIterator<AHampiLootItem> It(GetWorld()); It; ++It)
			{
				const float DistSq = FVector::DistSquared(Soldier->GetActorLocation(), (*It)->GetActorLocation());
				if ((*It)->IsAvailable() && DistSq < BestLootDistSq)
				{
					BestLootDistSq = DistSq;
					NearestLoot = *It;
				}
			}
			PromptText = NearestLoot
				? TEXT("LOOT NEARBY - WALK OVER TO COLLECT")
				: TEXT("FIND THE M416 AND LOOT BEFORE THE ZONE SHRINKS");
		}
	}
	else
	{
		PromptText = Soldier->IsHealing() ? TEXT("HEALING IN PROGRESS") : TEXT("FIRE / ADS - WATCH THE SAFE ZONE");
	}
	if (PromptTextWidget)
	{
		PromptTextWidget->SetText(FText::FromString(PromptText));
	}

	UpdateCompass();
	UpdateRadar();
}

void UHampiMobileHUDWidget::UpdateCompass()
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || CompassTicks.Num() != 5)
	{
		return;
	}

	float Yaw = FRotator::NormalizeAxis(PC->GetControlRotation().Yaw);
	if (Yaw < 0.0f)
	{
		Yaw += 360.0f;
	}
	for (int32 i = 0; i < CompassTicks.Num(); ++i)
	{
		const float TickYaw = Yaw + (i - 2) * 30.0f;
		const FString Cardinal = CardinalFromYaw(TickYaw);
		const FString Label = i == 2
			? FString::Printf(TEXT("%s %d"), *Cardinal, FMath::RoundToInt(Yaw))
			: Cardinal;
		CompassTicks[i]->SetText(FText::FromString(Label));
		if (i == 2)
		{
			CompassText = Label;
		}
	}
}

void UHampiMobileHUDWidget::UpdateRadar()
{
	AHampiSoldierCharacter* Soldier = GetSoldier();
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!Soldier || !PC || !RadarOuterSlot)
	{
		return;
	}

	const FVector2D Center = AnchorCenterLocal(RadarOuterSlot);
	if (RadarPlayerDotSlot)
	{
		RadarPlayerDotSlot->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f));
		RadarPlayerDotSlot->SetPosition(Center - FVector2D(4.0f, 4.0f));
	}
	if (RadarPlayerDot)
	{
		RadarPlayerDot->SetVisibility(ESlateVisibility::HitTestInvisible);
	}

	const float YawRad = FMath::DegreesToRadians(PC->GetControlRotation().Yaw);
	const float CosYaw = FMath::Cos(YawRad);
	const float SinYaw = FMath::Sin(YawRad);
	const FVector PlayerLoc = Soldier->GetActorLocation();

	auto WorldToRadar = [&](const FVector& WorldLocation) -> FVector2D
	{
		const FVector Rel = WorldLocation - PlayerLoc;
		const float X = Rel.X * CosYaw + Rel.Y * SinYaw;
		const float Y = -Rel.X * SinYaw + Rel.Y * CosYaw;
		return Center + FVector2D(X, -Y) / HampiHUD::RadarRangeCm * HampiHUD::RadarRadiusPx;
	};

	TArray<AActor*> BotActors;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AHampiAICharacter::StaticClass(), BotActors);
	RadarVisibleDotCount = 0;
	for (int32 i = 0; i < RadarDots.Num(); ++i)
	{
		if (i >= BotActors.Num() || !BotActors[i])
		{
			RadarDots[i]->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const FVector2D Screen = WorldToRadar(BotActors[i]->GetActorLocation());
		const bool bInside = (Screen - Center).Size() <= HampiHUD::RadarRadiusPx;
		RadarDots[i]->SetVisibility(bInside ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		RadarDotSlots[i]->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f));
		RadarDotSlots[i]->SetPosition(Screen - FVector2D(3.5f, 3.5f));
		if (bInside)
		{
			++RadarVisibleDotCount;
		}
	}

	TArray<AActor*> Zones;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AHampiSafeZone::StaticClass(), Zones);
	AHampiSafeZone* Zone = Zones.Num() > 0 ? Cast<AHampiSafeZone>(Zones[0]) : nullptr;
	const FVector2D ZoneCenterPx = Zone ? WorldToRadar(Zone->GetActorLocation()) : Center;
	const float ZoneRadiusPx = Zone ? Zone->GetCurrentRadius() / HampiHUD::RadarRangeCm * HampiHUD::RadarRadiusPx : 0.0f;
	for (int32 i = 0; i < ZoneRingSegments.Num(); ++i)
	{
		if (!Zone || ZoneRadiusPx <= 0.0f)
		{
			ZoneRingSegments[i]->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const float Angle = 2.0f * PI * static_cast<float>(i) / static_cast<float>(ZoneRingSegments.Num());
		const FVector2D Point = ZoneCenterPx + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * ZoneRadiusPx;
		const bool bInside = (Point - Center).Size() <= HampiHUD::RadarRadiusPx;
		ZoneRingSegments[i]->SetVisibility(bInside ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		ZoneRingSlots[i]->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 0.0f));
		ZoneRingSlots[i]->SetPosition(Point - FVector2D(2.5f, 2.5f));
	}
}

void UHampiMobileHUDWidget::SimulateTouchButton(const FString& ButtonName, bool bPressed)
{
	const FString Name = ButtonName.ToUpper();
	if (!Buttons.Contains(Name))
	{
		return;
	}
	SetButtonStateAndPress(Name, bPressed);
}

void UHampiMobileHUDWidget::SimulateMovementTouch(float CenterXNorm, float CenterYNorm, float DeltaXNorm, float DeltaYNorm)
{
	bMoveTouchActive = true;
	MovePointerIndex = 99;
	const FVector2D Center = LocalFromNorm(CenterXNorm, CenterYNorm);
	MoveTouchStart = Center;
	MoveTouchCurrent = Center;
	SetJoystickCenter(Center);
	MoveX = FMath::Clamp(DeltaXNorm, -1.0f, 1.0f);
	MoveY = FMath::Clamp(-DeltaYNorm, -1.0f, 1.0f);
	UpdateJoystickVisual();
}

void UHampiMobileHUDWidget::SimulateCameraSwipe(float DeltaXPixels, float DeltaYPixels)
{
	bCameraTouchActive = true;
	CameraPointerIndex = 99;
	ApplyCameraDelta(DeltaXPixels, DeltaYPixels);
}

void UHampiMobileHUDWidget::EndSimulatedTouches()
{
	bMoveTouchActive = false;
	bCameraTouchActive = false;
	MovePointerIndex = -1;
	CameraPointerIndex = -1;
	MoveX = 0.0f;
	MoveY = 0.0f;
	UpdateJoystickVisual();
}

FString UHampiMobileHUDWidget::GetHUDStateSummary() const
{
	AHampiSoldierCharacter* Soldier = GetSoldier();
	const FString ActiveSlot = Soldier ? Soldier->GetActiveWeaponSlot() : TEXT("None");
	return FString::Printf(TEXT("MOVE=%.2f,%.2f JOYSTICK=%d YAW_DELTA=%.1f PITCH_DELTA=%.1f "
		"FIRE=%d ADS=%d JUMP=%d CROUCH=%d RELOAD=%d SWAP=%d SLOT=%s HP=%.2f SHIELD=%.2f "
		"RADAR=%d/%d BUTTONS=%d AMMO=%s PROMPT=%s COMPASS=%s"),
		MoveX, MoveY, bMoveTouchActive ? 1 : 0, TotalCameraYawDelta, TotalCameraPitchDelta,
		IsButtonPressed(TEXT("FIRE")) ? 1 : 0, IsButtonPressed(TEXT("ADS")) ? 1 : 0,
		IsButtonPressed(TEXT("JUMP")) ? 1 : 0, IsButtonPressed(TEXT("CROUCH")) ? 1 : 0,
		IsButtonPressed(TEXT("RELOAD")) ? 1 : 0, IsButtonPressed(TEXT("SWAP")) ? 1 : 0,
		*ActiveSlot, GetHealthBarPercent(), GetShieldBarPercent(),
		RadarVisibleDotCount, RadarDots.Num(), GetButtonCount(), *AmmoText, *PromptText, *CompassText);
}

bool UHampiMobileHUDWidget::IsButtonPressed(const FString& ButtonName) const
{
	const bool* Found = ButtonPressStates.Find(ButtonName.ToUpper());
	return Found ? *Found : false;
}

int32 UHampiMobileHUDWidget::GetButtonPressCount(const FString& ButtonName) const
{
	const int32* Found = ButtonPressCounts.Find(ButtonName.ToUpper());
	return Found ? *Found : 0;
}

float UHampiMobileHUDWidget::GetHealthBarPercent() const
{
	return HealthBar ? HealthBar->GetPercent() : 0.0f;
}

float UHampiMobileHUDWidget::GetShieldBarPercent() const
{
	return ShieldBar ? ShieldBar->GetPercent() : 0.0f;
}

void UHampiMobileHUDWidget::SetButtonStateAndPress(const FString& ButtonName, bool bPressed)
{
	ButtonPressStates.Add(ButtonName, bPressed);
	if (!bPressed)
	{
		if (ButtonName == TEXT("FIRE")) { HandleFireReleased(); }
		else if (ButtonName == TEXT("ADS")) { HandleAimReleased(); }
		else if (ButtonName == TEXT("JUMP")) { HandleJumpReleased(); }
		return;
	}

	ButtonPressCounts.Add(ButtonName, GetButtonPressCount(ButtonName) + 1);

	if (ButtonName == TEXT("FIRE")) { HandleFirePressed(); }
	else if (ButtonName == TEXT("ADS")) { HandleAimPressed(); }
	else if (ButtonName == TEXT("JUMP")) { HandleJumpPressed(); }
	else if (ButtonName == TEXT("CROUCH")) { HandleCrouchPressed(); }
	else if (ButtonName == TEXT("RELOAD")) { HandleReloadPressed(); }
	else if (ButtonName == TEXT("SWAP")) { HandleSwapPressed(); }
}

void UHampiMobileHUDWidget::HandleFirePressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->StartM416Fire();
	}
}

void UHampiMobileHUDWidget::HandleFireReleased()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->StopM416Fire();
	}
}

void UHampiMobileHUDWidget::HandleAimPressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->StartM416Aim();
	}
}

void UHampiMobileHUDWidget::HandleAimReleased()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->StopM416Aim();
	}
}

void UHampiMobileHUDWidget::HandleJumpPressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->MobileJump();
	}
}

void UHampiMobileHUDWidget::HandleJumpReleased()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->MobileStopJump();
	}
}

void UHampiMobileHUDWidget::HandleCrouchPressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->TogglePlayerCrouch();
	}
}

void UHampiMobileHUDWidget::HandleReloadPressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->ReloadM416();
	}
}

void UHampiMobileHUDWidget::HandleSwapPressed()
{
	if (AHampiSoldierCharacter* Soldier = GetSoldier())
	{
		Soldier->CycleWeaponSlot();
	}
}
