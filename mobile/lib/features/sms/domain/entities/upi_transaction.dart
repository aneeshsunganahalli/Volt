/// Represents a UPI transaction extracted from SMS
class UpiTransaction {
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

  UpiTransaction({
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

  Map<String, dynamic> toJson() {
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

  @override
  String toString() {
    return 'UpiTransaction{amount: $amount, merchant: $merchant, type: $type, transactionId: $transactionId}';
  }
}

enum TransactionType {
  credit,
  debit,
  unknown,
}
