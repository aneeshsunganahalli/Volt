import 'package:dartz/dartz.dart';
import '../../../../core/error/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../repositories/sms_repository.dart';

class HasSmsPermissionsUseCase implements UseCase<bool, NoParams> {
  final SmsRepository repository;

  HasSmsPermissionsUseCase(this.repository);

  @override
  Future<Either<Failure, bool>> call(NoParams params) async {
    return await repository.hasPermissions();
  }
}
