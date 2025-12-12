import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'core/theme/app_pallette.dart';
import 'core/navigation/main_navigator.dart';
import 'core/widgets/state_widgets.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'features/auth/presentation/bloc/auth_event.dart';
import 'features/auth/presentation/bloc/auth_state.dart';
import 'features/auth/presentation/pages/login_page.dart';
import 'init_dependencies.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initDependencies();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => sl<AuthBloc>()..add(CheckAuthStatusEvent()),
      child: MaterialApp(
        title: 'Volt',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: AppColorScheme.lightColorScheme,
          scaffoldBackgroundColor: ColorPalette.backgroundLight,
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: AppColorScheme.darkColorScheme,
          scaffoldBackgroundColor: ColorPalette.backgroundDark,
          useMaterial3: true,
        ),
        themeMode: ThemeMode.system,
        home: const AuthWrapper(),
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        if (state is AuthLoading || state is AuthInitial) {
          return const Scaffold(
            body: LoadingState(message: 'Checking your account...'),
          );
        } else if (state is AuthAuthenticated) {
          return const MainNavigator();
        } else {
          return const LoginPage();
        }
      },
    );
  }
}
