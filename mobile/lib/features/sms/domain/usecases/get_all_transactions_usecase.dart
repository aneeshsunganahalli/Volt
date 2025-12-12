import 'package:dartz/dartz.dart';
import 'package:equatable/equatable.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/transaction.dart';
import '../repositories/sms_repository.dart';

class GetAllTransactionsUseCase implements UseCase<List<Transaction>, GetTransactionsParams> {
  final SmsRepository repository;

  GetAllTransactionsUseCase(this.repository);

  @override
  Future<Either<Failure, List<Transaction>>> call(GetTransactionsParams params) async {
    return await repository.getAllTransactions(limit: params.limit);
  }
}

class GetTransactionsParams extends Equatable {
  final int? limit;

  const GetTransactionsParams({this.limit});

  @override
  List<Object?> get props => [limit];
}
