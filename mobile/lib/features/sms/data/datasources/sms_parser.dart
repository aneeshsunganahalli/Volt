import '../../../../core/services/parsers/bank_parser_factory.dart';
import '../models/transaction_model.dart';
import '../../domain/entities/transaction.dart';

class SmsParser {
  // Bank parser factory for bank-specific parsing
  static final BankParserFactory _parserFactory = BankParserFactory();
  
  // Common UPI keywords to identify UPI transactions
  static const List<String> upiKeywords = [
    'UPI',
    'credited',
    'debited',
    'paid',
    'received',
    'transferred',
    'transaction',
    'A/c',
    'Rs.',
    'INR',
  ];

  // Common bank sender IDs
  static const List<String> bankSenderIds = [
    'HDFC',
    'ICICI',
    'SBI',
    'SBIINB',
    'SBMSMS',
    'SBIUPI',
    'AXIS',
    'KOTAK',
    'PAYTM',
    'PHONEPE',
    'GPAY',
    'GOOGLEPAY',
    'BHIM',
    'IDFC',
    'YESBNK',
    'FEDBNK',
    'INDUS',
    'PNBSMS',
    'BOBSMS',
    'CANBNK',
    'UNIONB',
    'ANDBNK',
    'BARODAM',
    'IOBSMS',
    'CBSSBI',
    'HDFCBK',
    'ICICIB',
    'AXIBNK',
  ];

  static bool isBankSms(String message, {String? sender, String? address}) {
    final upperMessage = message.toUpperCase();
    
    // Check sender ID if provided - handle both official IDs and contact names
    // Check both resolved sender name and raw address
    if (sender != null || address != null) {
      final upperSender = (sender ?? '').toUpperCase();
      final upperAddr = (address ?? '').toUpperCase();
      final normalizedSender = upperSender.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      final normalizedAddr = upperAddr.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      // Direct bank ID match against normalized sender name
      for (var bankId in bankSenderIds) {
        if (normalizedSender.contains(bankId) || normalizedAddr.contains(bankId)) {
          print('✅ Bank sender detected: ${sender ?? address} (matched: $bankId)');
          return true;
        }
      }
      
      // Also accept if sender contains bank-related keywords (for contacts)
      if (upperSender.contains('BANK') || upperSender.contains('UPI') || upperSender.contains('PAY') ||
          upperAddr.contains('BANK') || upperAddr.contains('UPI') || upperAddr.contains('PAY')) {
        print('✅ Bank sender detected: ${sender ?? address} (banking keyword)');
        return true;
      }
    }
    
    // Check if message contains amount indicators - be more flexible
    final hasAmount = RegExp(
      r'(?:RS\.?|INR|₹)\s*[\d,]+(?:\.\d{1,2})?|(?:debited|credited|paid|received)\s+(?:by|of|for)?\s*[\d,]+(?:\.\d{1,2})?', 
      caseSensitive: false
    ).hasMatch(message);
    
    if (!hasAmount) {
      return false;
    }

    // Filter out promotional and marketing messages that contain amounts (e.g. offers, recharge, plans)
    final promoIndicators = [
      'UPGRADE', 'OFFER', 'OFF', 'SALE', 'GET', 'CLICK', 'DOWNLOAD', 'RECHARGE', 'PLAN', 'TOPUP', 'GB', 'MB', 'ROLOVER', 'ROLL', 'LIMITED', 'PROMO', 'PROMOTION', 'LINK', 'https://', 'HTTP://', 'WWW.', 'BUY', 'SUBSCRIBE'
    ];

    bool isPromo = false;
    for (var kw in promoIndicators) {
      if (upperMessage.contains(kw)) {
        isPromo = true;
        break;
      }
    }

    // If it's clearly promotional and the sender is not a known bank ID, don't mark it as bank SMS
    if (isPromo && (sender != null || address != null)) {
      final upperSender = (sender ?? '').toUpperCase();
      final upperAddr = (address ?? '').toUpperCase();
      final normalizedSender = upperSender.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      final normalizedAddr = upperAddr.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      var isKnownBankSender = false;
      for (var bankId in bankSenderIds) {
        if (normalizedSender.contains(bankId) || normalizedAddr.contains(bankId)) {
          isKnownBankSender = true;
          break;
        }
      }
          if (!isKnownBankSender) {
        print('❌ Promotional message detected: skipping (sender: $sender)');
        return false;
      }
    }
    
    // Check for banking keywords - be more comprehensive
    final bankingKeywords = [
      'UPI',
      'CREDITED',
      'DEBITED',
      'DEBIT',
      'CREDIT',
      'A/C',
      'ACCOUNT',
      'ACC',
      'TRANSACTION',
      'TXN',
      'TRANSFERRED',
      'TRANSFER',
      'WITHDRAWN',
      'DEPOSITED',
      'BALANCE',
      'PAID',
      'RECEIVED',
      'PURCHASE',
      'PAYMENT',
    ];
    
    for (var keyword in bankingKeywords) {
      if (upperMessage.contains(keyword)) {
        // If we have a banking keyword but the message contains promo indicators and the
        // sender is not a known bank, treat as non-bank message.
          if (isPromo && (sender != null || address != null)) {
          final upperSender = (sender ?? '').toUpperCase();
          final upperAddr = (address ?? '').toUpperCase();
          final normalizedSender = upperSender.replaceAll(RegExp(r'[^A-Z0-9]'), '');
          final normalizedAddr = upperAddr.replaceAll(RegExp(r'[^A-Z0-9]'), '');
          var isKnownBankSender = false;
          for (var bankId in bankSenderIds) {
            if (normalizedSender.contains(bankId) || normalizedAddr.contains(bankId)) {
              isKnownBankSender = true;
              break;
            }
          }
          if (!isKnownBankSender) {
            print('❌ Banking keyword found but looks promotional and sender is not bank: $keyword');
            continue; // keep checking other keywords
          }
        }
        print('✅ Banking keyword found: $keyword');
        return true;
      }
    }
    
    print('❌ Not a bank SMS - no banking keywords found');
    print('   Sender: ${sender ?? address}');
    print('   Preview: ${message.substring(0, message.length > 60 ? 60 : message.length)}...');
    return false;
  }

  /// Validates if the message is a completed transaction (not a request)
  static bool isValidTransaction(String message) {
    final upperMessage = message.toUpperCase();
    
    // Check if message contains amount indicators - more flexible matching
    final hasAmount = RegExp(
      r'(?:RS\.?|INR|₹)\s*[\d,]+(?:\.\d{1,2})?|(?:debited|credited|paid|received)\s+(?:by|of|for)?\s*[\d,]+(?:\.\d{1,2})?',
      caseSensitive: false
    ).hasMatch(message);
    
    if (!hasAmount) {
      print('❌ REJECTED: No amount in message');
      return false;
    }
    
    // CRITICAL: Filter out money requests and collect requests
    final requestKeywords = [
      'REQUEST',
      'COLLECT',
      'PENDING',
      'REQUESTED',
      'REQUESTING',
      'WAITING',
      'APPROVE',
      'ACCEPT',
      'DECLINE',
      'REJECT',
      'AUTHORIZATION',
      'AWAITING',
      'SCHEDULED',
      'REMIND',
      'REMINDER',
      'RECHARGE NOW', // Promotional messages
      'SPECIAL OFFER', // Promotional messages
      'PLAN IS EXPIRING', // Promotional messages
    ];
    
    for (var keyword in requestKeywords) {
      if (upperMessage.contains(keyword)) {
        print('❌ REJECTED: Money request detected - keyword "$keyword"');
        print('   Message: ${message.substring(0, message.length > 60 ? 60 : message.length)}...');
        return false; // This is a request, not a completed transaction
      }
    }
    
    // Check for confirmed transaction keywords - must indicate completed action
    final transactionKeywords = [
      'CREDITED',
      'DEBITED',
      'PAID TO',
      'PAID AT', 
      'PAID FOR',
      'RECEIVED FROM',
      'TRANSFERRED TO',
      'TRANSFERRED FROM',
      'DEPOSITED',
      'WITHDRAWN',
      'PURCHASE AT',
      'PURCHASE FROM',
      'SPENT AT',
      'DEBIT FROM', // SBI specific pattern
      'CREDIT TO',
      'DEBIT OF',
      'CREDIT OF',
    ];
    
    for (var keyword in transactionKeywords) {
      if (upperMessage.contains(keyword)) {
        print('✅ ACCEPTED: Completed transaction - keyword "$keyword"');
        return true;
      }
    }
    
    // Special case: Government subsidies (these are actual money transfers)
    if (upperMessage.contains('SUBSIDY') && upperMessage.contains('SENT')) {
      print('✅ ACCEPTED: Government subsidy transaction');
      return true;
    }
    
    // Additional check: if it looks promotional (contains URLs or common promo keywords), reject
    final promoIndicators = [
      'UPGRADE', 'OFFER', 'OFF', 'SALE', 'GET', 'CLICK', 'DOWNLOAD', 'RECHARGE', 'PLAN', 'TOPUP', 'GB', 'MB', 'ROLOVER', 'ROLL', 'LIMITED', 'PROMO', 'PROMOTION', 'LINK', 'https://', 'HTTP://', 'WWW.'
    ];
    for (var kw in promoIndicators) {
      if (upperMessage.contains(kw)) {
        print('❌ REJECTED: Promotional message detected (keyword: $kw)');
        return false;
      }
    }

    print('❌ REJECTED: No transaction keyword found');
    print('   Message preview: ${message.substring(0, message.length > 100 ? 100 : message.length)}...');
    return false;
  }

  static TransactionModel? parseTransaction(
    String message, {
    required DateTime timestamp,
    String? sender,
    String? address,
  }) {
    // First check if it's from a bank
    if (!isBankSms(message, sender: sender, address: address)) {
      return null;
    }

    // CRITICAL: Validate it's a completed transaction, not a request
    if (!isValidTransaction(message)) {
      return null;
    }

    print('📝 PARSING: ${message.substring(0, message.length > 80 ? 80 : message.length)}...');

    // Try bank-specific parser first for best accuracy
    final bankParsed = _parserFactory.parse(
      message,
      sender: sender,
      address: address,
      timestamp: timestamp,
    );
    
    if (bankParsed != null) {
      // Convert UpiTransaction to TransactionModel
      // Map TransactionType from upi_transaction to transaction domain entity
      TransactionType mappedType = TransactionType.unknown;
      if (bankParsed.type.toString() == 'TransactionType.credit') {
        mappedType = TransactionType.credit;
      } else if (bankParsed.type.toString() == 'TransactionType.debit') {
        mappedType = TransactionType.debit;
      }
      
      return TransactionModel(
        amount: bankParsed.amount,
        merchant: bankParsed.merchant,
        upiId: bankParsed.upiId,
        transactionId: bankParsed.transactionId,
        timestamp: bankParsed.timestamp,
        type: mappedType,
        balance: bankParsed.balance,
        bankName: bankParsed.bankName,
        rawMessage: bankParsed.rawMessage,
      );
    }

    print('⚠️ Bank-specific parser failed, using generic fallback');

    final upperMessage = message.toUpperCase();
    
    // Determine transaction type with enhanced detection
    // Credit keywords take priority over ambiguous keywords like SENT
    TransactionType type = TransactionType.unknown;
    
    // Check for CREDIT first (these are unambiguous)
    if (upperMessage.contains('CREDITED') || 
        upperMessage.contains('CREDIT TO') ||
        upperMessage.contains('RECEIVED') ||
        upperMessage.contains('DEPOSITED') ||
        upperMessage.contains('SUBSIDY') || // Subsidies are money received
        upperMessage.contains('REFUND') ||   // Refunds are money received
        upperMessage.contains('CASHBACK') ||
        (upperMessage.contains('CREDIT') && !upperMessage.contains('DEBIT'))) {
      type = TransactionType.credit;
      print('   Type: CREDIT');
    } 
    // Then check for DEBIT (these are unambiguous)
    else if (upperMessage.contains('DEBITED') || 
             upperMessage.contains('DEBIT FROM') ||
             upperMessage.contains('DEBIT OF') ||
             upperMessage.contains('WITHDRAWN') ||
             upperMessage.contains('PAID TO') ||
             upperMessage.contains('PAID AT') ||
             upperMessage.contains('PAID FOR') ||
             upperMessage.contains('PURCHASE AT') ||
             upperMessage.contains('PURCHASE FROM') ||
             upperMessage.contains('SPENT') ||
             (upperMessage.contains('DEBIT') && !upperMessage.contains('CREDIT'))) {
      type = TransactionType.debit;
      print('   Type: DEBIT');
    }
    // Handle ambiguous cases like SENT/TRANSFERRED by checking context
    else if (upperMessage.contains('SENT') || 
             upperMessage.contains('PAID') ||
             upperMessage.contains('TRANSFERRED') ||
             upperMessage.contains('TRANSFER')) {
      // If it says "sent to you" or "transfer from", it's credit
      if (upperMessage.contains('TO YOU') || 
          upperMessage.contains('TO YOUR') ||
          upperMessage.contains('TRANSFER FROM')) {
        type = TransactionType.credit;
        print('   Type: CREDIT (from context)');
      } else {
        type = TransactionType.debit;
        print('   Type: DEBIT (from context)');
      }
    } else {
      print('   Type: UNKNOWN - Keywords not found');
    }

    // Extract amount - handle both with and without currency symbols
    String? amount;
    final amountPatterns = [
      // With currency symbol: Rs.500, INR 1234.56, ₹999
      RegExp(r'(?:RS\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)', caseSensitive: false),
      // Without currency: "debited by 40.0", "credited by 350"
      RegExp(r'(?:debited|credited|paid|received)\s+(?:by|of|for)?\s*([\d,]+(?:\.\d{1,2})?)', caseSensitive: false),
    ];
    
    for (var pattern in amountPatterns) {
      final match = pattern.firstMatch(message);
      if (match != null) {
        amount = match.group(1)?.replaceAll(',', '');
        break;
      }
    }

    // Extract UPI ID
    final upiRegex = RegExp(r'([a-zA-Z0-9.\-_]+@[a-zA-Z]+)', caseSensitive: false);
    final upiMatch = upiRegex.firstMatch(message);
    final upiId = upiMatch?.group(1);

    // Extract transaction ID
    final txnRegex = RegExp(r'(?:UPI Ref No|Ref No|RefNo|TxnId|TransactionId)[:\s]+([A-Z0-9]+)', caseSensitive: false);
    final txnMatch = txnRegex.firstMatch(message);
    final transactionId = txnMatch?.group(1);

    // Extract merchant/beneficiary name
    String? merchant;
    final merchantPatterns = [
      RegExp(r'(?:to|from|at)\s+([A-Z][A-Za-z\s]+)(?:\s+on|\s+UPI|\s+Rs)', caseSensitive: false),
      RegExp(r'(?:paid to|received from)\s+([A-Z][A-Za-z\s]+)', caseSensitive: false),
    ];
    
    for (var pattern in merchantPatterns) {
      final match = pattern.firstMatch(message);
      if (match != null) {
        merchant = match.group(1)?.trim();
        break;
      }
    }

    // Extract balance
    final balanceRegex = RegExp(r'(?:Avl (?:Bal|Balance)|Available Balance|Bal)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)', caseSensitive: false);
    final balanceMatch = balanceRegex.firstMatch(message);
    final balance = balanceMatch?.group(1)?.replaceAll(',', '');

    // Extract bank name from sender
    String? bankName;
    // Determine bank name by checking both sender display name and the raw address
    if (sender != null || address != null) {
      final upperSender = (sender ?? '').toUpperCase();
      final upperAddr = (address ?? '').toUpperCase();
      final normalizedSender = upperSender.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      final normalizedAddr = upperAddr.replaceAll(RegExp(r'[^A-Z0-9]'), '');
      for (var bankId in bankSenderIds) {
        if (normalizedSender.contains(bankId) || normalizedAddr.contains(bankId)) {
          bankName = bankId;
          break;
        }
      }
    }

    // Extract transaction date from message body
    DateTime transactionDate = timestamp; // Default to SMS timestamp
    
    // Try to extract date from various patterns
    final datePatterns = [
      // Pattern: "on date 03Dec25", "on date 29Nov25"
      RegExp(r'on date (\d{2})([A-Za-z]{3})(\d{2})', caseSensitive: false),
      // Pattern: "on 06-12-2025", "on 03-Dec-25"
      RegExp(r'on (\d{2})[/-](\d{2}|\w{3})[/-](\d{2,4})', caseSensitive: false),
      // Pattern: "dated 03-12-2025"
      RegExp(r'dated (\d{2})[/-](\d{2}|\w{3})[/-](\d{2,4})', caseSensitive: false),
    ];
    
    for (var pattern in datePatterns) {
      final match = pattern.firstMatch(message);
      if (match != null) {
        try {
          final day = int.parse(match.group(1)!);
          final monthStr = match.group(2)!;
          final yearStr = match.group(3)!;
          
          // Parse month (either numeric or abbreviated name)
          int month;
          if (RegExp(r'^\d+$').hasMatch(monthStr)) {
            month = int.parse(monthStr);
          } else {
            // Convert month abbreviation to number
            final monthMap = {
              'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
              'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
              'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            };
            month = monthMap[monthStr.toLowerCase()] ?? DateTime.now().month;
          }
          
          // Parse year (handle 2-digit years)
          int year = int.parse(yearStr);
          if (year < 100) {
            year += 2000;
          }
          
          transactionDate = DateTime(year, month, day);
          print('   Extracted transaction date: ${transactionDate.toString().split(' ')[0]}');
        } catch (e) {
          print('   Failed to parse date: $e');
          // Keep using SMS timestamp as fallback
        }
        break;
      }
    }

    return TransactionModel(
      amount: amount,
      merchant: merchant,
      upiId: upiId,
      transactionId: transactionId,
      timestamp: transactionDate,
      type: type,
      balance: balance,
      bankName: bankName,
      rawMessage: message,
    );
  }
}
