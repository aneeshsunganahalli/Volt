import '../../domain/entities/transaction.dart';

class TransactionModel extends Transaction {
  const TransactionModel({
    super.amount,
    super.merchant,
    super.upiId,
    super.transactionId,
    super.timestamp,
    required super.type,
    super.balance,
    super.bankName,
    super.accountNumber,
    required super.rawMessage,
  });

  factory TransactionModel.fromMap(Map<String, dynamic> map) {
    return TransactionModel(
      amount: map['amount'] as String?,
      merchant: map['merchant'] as String?,
      upiId: map['upiId'] as String?,
      transactionId: map['transactionId'] as String?,
      timestamp: map['timestamp'] != null
          ? DateTime.parse(map['timestamp'] as String)
          : null,
      type: _parseTransactionType(map['type'] as String?),
      balance: map['balance'] as String?,
      bankName: map['bankName'] as String?,
      accountNumber: map['accountNumber'] as String?,
      rawMessage: map['rawMessage'] as String? ?? '',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'amount': amount,
      'merchant': merchant,
      'upiId': upiId,
      'transactionId': transactionId,
      'timestamp': timestamp?.toIso8601String(),
      'type': type.toString(),
      'balance': balance,
      'bankName': bankName,
      'accountNumber': accountNumber,
      'rawMessage': rawMessage,
    };
  }

  static TransactionType _parseTransactionType(String? type) {
    if (type == null) return TransactionType.unknown;
    if (type.contains('credit')) return TransactionType.credit;
    if (type.contains('debit')) return TransactionType.debit;
    return TransactionType.unknown;
  }
}
