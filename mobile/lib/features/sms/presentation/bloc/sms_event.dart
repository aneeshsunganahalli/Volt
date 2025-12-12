import 'package:equatable/equatable.dart';

abstract class SmsEvent extends Equatable {
  const SmsEvent();

  @override
  List<Object?> get props => [];
}

class RequestSmsPermissionEvent extends SmsEvent {}

class CheckSmsPermissionEvent extends SmsEvent {}

class LoadTransactionsEvent extends SmsEvent {
  final int? limit;

  const LoadTransactionsEvent({this.limit});

  @override
  List<Object?> get props => [limit];
}

class RefreshTransactionsEvent extends SmsEvent {}

class StartListeningToIncomingSmsEvent extends SmsEvent {}

class StopListeningToIncomingSmsEvent extends SmsEvent {}

class NewIncomingTransactionEvent extends SmsEvent {
  final dynamic transaction;
  
  const NewIncomingTransactionEvent(this.transaction);
  
  @override
  List<Object?> get props => [transaction];
}
