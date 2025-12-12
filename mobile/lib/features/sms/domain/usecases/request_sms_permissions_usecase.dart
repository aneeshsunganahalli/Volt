import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../repositories/sms_repository.dart';

class RequestSmsPermissionsUseCase implements UseCase<bool, NoParams> {
  final SmsRepository repository;

  RequestSmsPermissionsUseCase(this.repository);

  @override
  Future<Either<Failure, bool>> call(NoParams params) async {
    return await repository.requestSmsPermissions();
  }
}
