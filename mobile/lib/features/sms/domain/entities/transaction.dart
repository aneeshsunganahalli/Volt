import 'package:equatable/equatable.dart';

enum TransactionType {
  credit,
  debit,
  unknown,
}

class Transaction extends Equatable {
  final String? amount;
  final String? merchant;
  final String? upiId;
  final String? transactionId;
  final DateTime? timestamp;
  final TransactionType type;
  final String? balance;
  final String? bankName;
  final String? accountNumber;
  final String rawMessage;

  const Transaction({
    this.amount,
    this.merchant,
    this.upiId,
    this.transactionId,
    this.timestamp,
    required this.type,
    this.balance,
    this.bankName,
    this.accountNumber,
    required this.rawMessage,
  });

  @override
  List<Object?> get props => [
        amount,
        merchant,
        upiId,
        transactionId,
        timestamp,
        type,
        balance,
        bankName,
        accountNumber,
        rawMessage,
      ];
}
