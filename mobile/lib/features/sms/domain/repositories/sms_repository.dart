import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../entities/transaction.dart';

abstract class SmsRepository {
  Future<Either<Failure, bool>> requestSmsPermissions();
  Future<Either<Failure, bool>> hasPermissions();
  Future<Either<Failure, List<Transaction>>> getAllTransactions({int? limit});
  Future<Either<Failure, Stream<Transaction>>> listenToIncomingSms();
}
