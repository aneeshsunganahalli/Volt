import 'package:flutter/material.dart';

/// ------------------------------------------------------------
/// SUPABASE THEME COLORS
/// ------------------------------------------------------------
// Brand colors
const brandColor = Color(0xFF3ECF8E); // Supabase green
const brandAccent = Color(0xFF1F1F1F); // Dark gray/black

// Background colors
const backgroundColor = Color(0xFF181818); // Dark background
const surfaceColor = Color(0xFF1F1F1F); // Slightly lighter surface
const cardColor = Color(0xFF262626); // Card background

// Text colors
const textColor = Color(0xFFEDEDED); // Light gray text
const textSecondaryColor = Color(0xFFA3A3A3); // Muted text
const textMutedColor = Color(0xFF737373); // Very muted text

// Accent colors
const accentColor = Color(0xFF3ECF8E); // Supabase green
const accentHoverColor = Color(0xFF2FB374); // Darker green on hover

// Border colors
const borderColor = Color(0xFF2E2E2E);
const borderLightColor = Color(0xFF3D3D3D);

// Semantic colors
const successColor = Color(0xFF3ECF8E); // Green
const errorColor = Color(0xFFF44336); // Red
const warningColor = Color(0xFFF59E0B); // Amber/Orange
const infoColor = Color(0xFF3B82F6); // Blue

/// ------------------------------------------------------------
/// COLOR SCHEME
/// ------------------------------------------------------------
const ColorScheme appColorScheme = ColorScheme(
  brightness: Brightness.dark,

  background: backgroundColor,
  onBackground: textColor,

  surface: surfaceColor,
  onSurface: textColor,

  primary: brandColor,
  onPrimary: Color(0xFF000000),

  secondary: brandAccent,
  onSecondary: textColor,

  tertiary: accentColor,
  onTertiary: Color(0xFF000000),

  error: errorColor,
  onError: Color(0xFFFFFFFF),

  outline: borderColor,
);

// Legacy ColorPalette class for backwards compatibility
class ColorPalette {
  ColorPalette._();

  // Base colors
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // Gray scale - Supabase style
  static const Color gray50 = Color(0xFFF9FAFB);
  static const Color gray100 = Color(0xFFEDEDED);
  static const Color gray200 = Color(0xFFD4D4D4);
  static const Color gray300 = Color(0xFFA3A3A3);
  static const Color gray400 = Color(0xFF737373);
  static const Color gray500 = Color(0xFF525252);
  static const Color gray600 = Color(0xFF3D3D3D);
  static const Color gray700 = Color(0xFF2E2E2E);
  static const Color gray800 = Color(0xFF262626);
  static const Color gray900 = Color(0xFF1F1F1F);

  // Brand colors
  static const Color green50 = Color(0xFFECFDF5);
  static const Color green100 = Color(0xFFD1FAE5);
  static const Color green200 = Color(0xFFA7F3D0);
  static const Color green300 = Color(0xFF6EE7B7);
  static const Color green400 = Color(0xFF3ECF8E); // Supabase green
  static const Color green500 = brandColor;
  static const Color green600 = Color(0xFF2FB374);
  static const Color green700 = Color(0xFF059669);
  static const Color green800 = Color(0xFF047857);
  static const Color green900 = Color(0xFF065F46);

  // Semantic colors
  static const Color success = successColor;
  static const Color successLight = Color(0xFFECFDF5);
  static const Color error = errorColor;
  static const Color errorLight = Color(0xFFFEE2E2);
  static const Color warning = warningColor;
  static const Color warningLight = Color(0xFFFEF3C7);
  static const Color info = infoColor;
  static const Color infoLight = Color(0xFFDFE8FF);

  // Orange/Amber (for warnings, highlights)
  static const Color orange50 = Color(0xFFFFF7ED);
  static const Color orange100 = Color(0xFFFFEDD5);
  static const Color orange200 = Color(0xFFFED7AA);
  static const Color orange300 = Color(0xFFFDBA74);
  static const Color orange400 = Color(0xFFFB923C);
  static const Color orange500 = warningColor;
  static const Color orange600 = Color(0xFFEA580C);
  static const Color orange700 = Color(0xFFC2410C);
  static const Color orange800 = Color(0xFF9A3412);
  static const Color orange900 = Color(0xFF7C2D12);

  // Blue (for info)
  static const Color blue50 = Color(0xFFEFF6FF);
  static const Color blue100 = Color(0xFFDBEAFE);
  static const Color blue200 = Color(0xFFBFDBFE);
  static const Color blue300 = Color(0xFF93C5FD);
  static const Color blue400 = Color(0xFF60A5FA);
  static const Color blue500 = infoColor;
  static const Color blue600 = Color(0xFF2563EB);
  static const Color blue700 = Color(0xFF1D4ED8);
  static const Color blue800 = Color(0xFF1E40AF);
  static const Color blue900 = Color(0xFF1E3A8A);

  // Positive/Negative for transactions
  static const Color positive = success; // Credit/Income
  static const Color negative = error; // Debit/Expense

  // Backgrounds
  static const Color backgroundLight = backgroundColor;
  static const Color backgroundDark = backgroundColor;
  static const Color surfaceLight = surfaceColor;
  static const Color surfaceDark = surfaceColor;

  // Text
  static const Color textPrimary = textColor;
  static const Color textSecondary = textSecondaryColor;
  static const Color textDisabled = textMutedColor;
  static const Color textPrimaryDark = textColor;
  static const Color textSecondaryDark = textSecondaryColor;

  // Borders
  static const Color borderLight = borderColor;
  static const Color borderDark = borderColor;

  // Effects
  static const Color shadow = Color(0x26000000); // Slightly darker for dark theme
  static const Color overlay = Color(0x80000000); // 50% opacity
}

class AppColorScheme {
  // Supabase dark theme
  static const ColorScheme lightColorScheme = appColorScheme;
  
  // Same theme for both modes (Supabase style is dark)
  static const ColorScheme darkColorScheme = appColorScheme;
}

/// Typography scale following 8pt grid system
class AppTypography {
  AppTypography._();

  // Titles
  static const TextStyle titleLarge = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    letterSpacing: -0.5,
  );

  static const TextStyle titleMedium = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.25,
  );

  static const TextStyle titleSmall = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
  );

  // Section headers
  static const TextStyle sectionHeader = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
  );

  // Body text
  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
  );

  // Labels/Meta
  static const TextStyle label = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
  );
}

/// Spacing scale (8pt grid)
class AppSpacing {
  AppSpacing._();

  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 16.0;
  static const double lg = 24.0;
  static const double xl = 32.0;
  static const double xxl = 48.0;
}


