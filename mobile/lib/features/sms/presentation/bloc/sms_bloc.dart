import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/usecases/usecase.dart';
import '../../domain/usecases/get_all_transactions_usecase.dart';
import '../../domain/usecases/has_sms_permissions_usecase.dart';
import '../../domain/usecases/request_sms_permissions_usecase.dart';
import 'sms_event.dart';
import 'sms_state.dart';

class SmsBloc extends Bloc<SmsEvent, SmsState> {
  final RequestSmsPermissionsUseCase requestSmsPermissionsUseCase;
  final HasSmsPermissionsUseCase hasSmsPermissionsUseCase;
  final GetAllTransactionsUseCase getAllTransactionsUseCase;
  StreamSubscription? _smsSubscription;

  SmsBloc({
    required this.requestSmsPermissionsUseCase,
    required this.hasSmsPermissionsUseCase,
    required this.getAllTransactionsUseCase,
  }) : super(SmsInitial()) {
    on<RequestSmsPermissionEvent>(_onRequestPermission);
    on<CheckSmsPermissionEvent>(_onCheckPermission);
    on<LoadTransactionsEvent>(_onLoadTransactions);
    on<RefreshTransactionsEvent>(_onRefreshTransactions);
    on<StartListeningToIncomingSmsEvent>(_onStartListening);
    on<StopListeningToIncomingSmsEvent>(_onStopListening);
    on<NewIncomingTransactionEvent>(_onNewIncomingTransaction);
  }

  Future<void> _onRequestPermission(
    RequestSmsPermissionEvent event,
    Emitter<SmsState> emit,
  ) async {
    final result = await requestSmsPermissionsUseCase(NoParams());

    result.fold(
      (failure) => emit(SmsError(failure.message)),
      (granted) {
        if (granted) {
          // Directly load transactions after permission is granted
          add(const LoadTransactionsEvent());
        } else {
          emit(SmsPermissionDenied());
        }
      },
    );
  }

  Future<void> _onCheckPermission(
    CheckSmsPermissionEvent event,
    Emitter<SmsState> emit,
  ) async {
    emit(SmsLoading());

    final result = await hasSmsPermissionsUseCase(NoParams());

    result.fold(
      (failure) => emit(SmsError(failure.message)),
      (hasPermission) {
        if (hasPermission) {
          add(const LoadTransactionsEvent());
        } else {
          emit(SmsPermissionDenied());
        }
      },
    );
  }

  Future<void> _onLoadTransactions(
    LoadTransactionsEvent event,
    Emitter<SmsState> emit,
  ) async {
    emit(SmsLoading());

    final result = await getAllTransactionsUseCase(
      GetTransactionsParams(limit: event.limit ?? 100),
    );

    result.fold(
      (failure) => emit(SmsError(failure.message)),
      (transactions) => emit(SmsTransactionsLoaded(transactions)),
    );
  }

  Future<void> _onRefreshTransactions(
    RefreshTransactionsEvent event,
    Emitter<SmsState> emit,
  ) async {
    final result = await getAllTransactionsUseCase(
      const GetTransactionsParams(limit: 100),
    );

    result.fold(
      (failure) => emit(SmsError(failure.message)),
      (transactions) => emit(SmsTransactionsLoaded(transactions)),
    );
  }

  void _onStartListening(
    StartListeningToIncomingSmsEvent event,
    Emitter<SmsState> emit,
  ) {
    // Auto-refresh will be handled by periodic checks or manual refresh
    // For now, this is a placeholder for future real-time SMS monitoring
  }

  void _onStopListening(
    StopListeningToIncomingSmsEvent event,
    Emitter<SmsState> emit,
  ) {
    _smsSubscription?.cancel();
    _smsSubscription = null;
  }

  Future<void> _onNewIncomingTransaction(
    NewIncomingTransactionEvent event,
    Emitter<SmsState> emit,
  ) async {
    // Refresh transactions when a new SMS arrives
    add(RefreshTransactionsEvent());
  }

  @override
  Future<void> close() {
    _smsSubscription?.cancel();
    return super.close();
  }
}
