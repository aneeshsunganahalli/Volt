import 'package:dartz/dartz.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../../core/error/exceptions.dart';
import '../../../../core/error/failures.dart';
import '../../domain/entities/transaction.dart';
import '../../domain/repositories/sms_repository.dart';
import '../datasources/sms_data_source.dart';
import '../datasources/sms_parser.dart';

class SmsRepositoryImpl implements SmsRepository {
  final SmsDataSource dataSource;

  SmsRepositoryImpl({required this.dataSource});

  @override
  Future<Either<Failure, bool>> requestSmsPermissions() async {
    try {
      final status = await Permission.sms.request();
      
      // If permission is permanently denied, guide user to settings
      if (status.isPermanentlyDenied) {
        await openAppSettings();
        return const Right(false);
      }
      
      return Right(status.isGranted);
    } catch (e) {
      return Left(ServerFailure('Failed to request permissions: ${e.toString()}'));
    }
  }

  @override
  Future<Either<Failure, bool>> hasPermissions() async {
    try {
      final status = await Permission.sms.status;
      return Right(status.isGranted);
    } catch (e) {
      return Left(ServerFailure('Failed to check permissions: ${e.toString()}'));
    }
  }

  @override
  Future<Either<Failure, List<Transaction>>> getAllTransactions({int? limit}) async {
    try {
      final messages = await dataSource.getInboxSms(limit: limit);
      print('📱 Total SMS messages fetched: ${messages.length}');
      print('=' * 80);
      final transactions = <Transaction>[];
      int creditCount = 0;
      int debitCount = 0;
      int messageIndex = 0;

      for (final message in messages) {
        messageIndex++;
        final address = message['address'] as String;
        final sender = message['sender'] as String? ?? address;
        final body = message['body'] as String;
        final dateMillis = message['date'] as int;
        final date = DateTime.fromMillisecondsSinceEpoch(dateMillis);

        print('\n📨 SMS #$messageIndex');
        print('From: ${sender} (address: $address)');
        print('Message: ${body}');
        print('-' * 80);

        final transaction = SmsParser.parseTransaction(
          body,
          timestamp: date,
          sender: sender,
          address: address,
        );

        if (transaction != null) {
          transactions.add(transaction);
          if (transaction.type == TransactionType.credit) {
            creditCount++;
          } else if (transaction.type == TransactionType.debit) {
            debitCount++;
          }
          print('✅ ADDED TO TRANSACTIONS\n');
        } else {
          print('❌ SKIPPED\n');
        }
      }

      print('=' * 80);
      print('✅ Valid transactions after filtering: ${transactions.length}');
      print('   💚 Credit transactions: $creditCount');
      print('   🔴 Debit transactions: $debitCount');
      print('=' * 80);
      return Right(transactions);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to get transactions: ${e.toString()}'));
    }
  }

  @override
  Future<Either<Failure, Stream<Transaction>>> listenToIncomingSms() async {
    try {
      final stream = dataSource.listenToIncomingSms();
      final transactionStream = stream.map((message) {
        final address = message['address'] as String;
        final sender = message['sender'] as String? ?? address;
        final body = message['body'] as String;
        final dateMillis = message['date'] as int;
        final date = DateTime.fromMillisecondsSinceEpoch(dateMillis);

        return SmsParser.parseTransaction(
          body,
          timestamp: date,
          sender: sender,
          address: address,
        );
      }).where((transaction) => transaction != null).cast<Transaction>();

      return Right(transactionStream);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to listen to SMS: ${e.toString()}'));
    }
  }
}
