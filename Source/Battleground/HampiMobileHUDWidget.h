#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "HampiMobileHUDWidget.generated.h"

class UButton;
class UCanvasPanel;
class UCanvasPanelSlot;
class UImage;
class UProgressBar;
class UTextBlock;
class UTexture2D;
class UWidget;
class AHampiSoldierCharacter;

/**
 * Native, asset-free mobile HUD. It is added to the viewport by the player soldier
 * at runtime, so the saved map and existing GameMode/camera/movement setup remain
 * unchanged. Mouse input mirrors touch input for desktop PIE testing.
 */
UCLASS()
class BATTLEGROUND_API UHampiMobileHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UHampiMobileHUDWidget(const FObjectInitializer& ObjectInitializer);

	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	virtual FReply NativeOnTouchStarted(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent) override;
	virtual FReply NativeOnTouchMoved(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent) override;
	virtual FReply NativeOnTouchEnded(const FGeometry& MyGeometry, const FPointerEvent& InTouchEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply NativeOnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

	/** Deterministic test hooks; these call the same handlers as real touches. */
	UFUNCTION(BlueprintCallable, Category = "Hampi HUD|Testing")
	void SimulateTouchButton(const FString& ButtonName, bool bPressed);

	UFUNCTION(BlueprintCallable, Category = "Hampi HUD|Testing")
	void SimulateMovementTouch(float CenterXNorm, float CenterYNorm, float DeltaXNorm, float DeltaYNorm);

	UFUNCTION(BlueprintCallable, Category = "Hampi HUD|Testing")
	void SimulateCameraSwipe(float DeltaXPixels, float DeltaYPixels);

	UFUNCTION(BlueprintCallable, Category = "Hampi HUD|Testing")
	void EndSimulatedTouches();

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	FString GetHUDStateSummary() const;

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	bool IsButtonPressed(const FString& ButtonName) const;

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetButtonCount() const { return 6; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetButtonPressCount(const FString& ButtonName) const;

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetCompassTickCount() const { return CompassTicks.Num(); }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetRadarDotCount() const { return RadarDots.Num(); }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetZoneRingSegmentCount() const { return ZoneRingSegments.Num(); }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	int32 GetRadarVisibleDotCount() const { return RadarVisibleDotCount; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetMoveX() const { return MoveX; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetMoveY() const { return MoveY; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	bool IsJoystickActive() const { return bMoveTouchActive; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetTotalCameraYawDelta() const { return TotalCameraYawDelta; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetTotalCameraPitchDelta() const { return TotalCameraPitchDelta; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetHealthBarPercent() const;

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	float GetShieldBarPercent() const;

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	FString GetPromptText() const { return PromptText; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	FString GetAmmoText() const { return AmmoText; }

	UFUNCTION(BlueprintPure, Category = "Hampi HUD|Testing")
	FString GetCompassText() const { return CompassText; }

private:
	void BuildLayout();
	void UpdateHUD();
	void UpdateCompass();
	void UpdateRadar();

	UCanvasPanelSlot* PlaceWidget(UWidget* Widget, FAnchors Anchors,
		FVector2D Position, FVector2D Size, FVector2D Alignment = FVector2D::ZeroVector);
	UImage* CreateColorImage(const FName& Name, const FLinearColor& Color,
		FAnchors Anchors, FVector2D Position, FVector2D Size, bool bHitTestInvisible = true);
	UTextBlock* CreateText(const FName& Name, const FString& Text,
		FAnchors Anchors, FVector2D Position, FVector2D Size, int32 FontSize = 12,
		bool bHitTestInvisible = true);
	UButton* CreateButton(const FName& Name, const FString& Label,
		FAnchors Anchors, FVector2D Position, FVector2D Size);
	FSlateBrush MakeColorBrush(const FLinearColor& Color) const;

	AHampiSoldierCharacter* GetSoldier() const;
	void ApplyMovementInput();
	void ApplyCameraDelta(float DeltaX, float DeltaY);
	void SetJoystickCenter(FVector2D LocalCenter);
	void UpdateJoystickVisual();
	void SetButtonStateAndPress(const FString& ButtonName, bool bPressed);

	FVector2D LocalFromNorm(float XNorm, float YNorm) const;
	FVector2D AnchorCenterLocal(UCanvasPanelSlot* Slot) const;
	static FString CardinalFromYaw(float YawDegrees);

	UFUNCTION() void HandleFirePressed();
	UFUNCTION() void HandleFireReleased();
	UFUNCTION() void HandleAimPressed();
	UFUNCTION() void HandleAimReleased();
	UFUNCTION() void HandleJumpPressed();
	UFUNCTION() void HandleJumpReleased();
	UFUNCTION() void HandleCrouchPressed();
	UFUNCTION() void HandleReloadPressed();
	UFUNCTION() void HandleSwapPressed();

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> WhiteTexture;

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanel> RootCanvas;

	UPROPERTY(Transient)
	TObjectPtr<UImage> MoveJoystickBase;

	UPROPERTY(Transient)
	TObjectPtr<UImage> MoveJoystickKnob;

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanelSlot> MoveJoystickBaseSlot;

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanelSlot> MoveJoystickKnobSlot;

	UPROPERTY(Transient)
	TObjectPtr<UProgressBar> HealthBar;

	UPROPERTY(Transient)
	TObjectPtr<UProgressBar> ShieldBar;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> HealthText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> ShieldText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> AmmoTextWidget;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> PromptTextWidget;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> StatusText;

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanelSlot> RadarOuterSlot;

	UPROPERTY(Transient)
	TObjectPtr<UImage> RadarPlayerDot;

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanelSlot> RadarPlayerDotSlot;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UTextBlock>> CompassTicks;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UImage>> RadarDots;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UCanvasPanelSlot>> RadarDotSlots;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UImage>> ZoneRingSegments;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UCanvasPanelSlot>> ZoneRingSlots;

	TMap<FString, UButton*> Buttons;
	TMap<FString, bool> ButtonPressStates;
	TMap<FString, int32> ButtonPressCounts;

	bool bLayoutBuilt = false;
	bool bMoveTouchActive = false;
	bool bCameraTouchActive = false;
	int32 MovePointerIndex = -1;
	int32 CameraPointerIndex = -1;
	FVector2D MoveTouchStart = FVector2D::ZeroVector;
	FVector2D MoveTouchCurrent = FVector2D::ZeroVector;
	FVector2D CameraTouchLast = FVector2D::ZeroVector;
	FVector2D JoystickCenter = FVector2D::ZeroVector;
	FVector2D ViewportSize = FVector2D(800.0f, 450.0f);

	float MoveX = 0.0f;
	float MoveY = 0.0f;
	float TotalCameraYawDelta = 0.0f;
	float TotalCameraPitchDelta = 0.0f;
	float MobileLookSensitivity = 0.12f;
	float JoystickRadius = 58.0f;
	int32 RadarVisibleDotCount = 0;

	FString PromptText = TEXT("");
	FString AmmoText = TEXT("");
	FString CompassText = TEXT("N");
};
