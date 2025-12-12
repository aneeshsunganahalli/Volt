import 'dart:async';
import 'package:flutter/services.dart';
import '../../../../core/error/exceptions.dart';

abstract class SmsDataSource {
  Future<bool> requestPermissions();
  Future<bool> hasPermissions();
  Future<List<Map<String, dynamic>>> getInboxSms({int? limit});
  Stream<Map<String, dynamic>> listenToIncomingSms();
}

class SmsDataSourceImpl implements SmsDataSource {
  static const MethodChannel _methodChannel = MethodChannel('sms_reader/methods');
  static const EventChannel _eventChannel = EventChannel('sms_reader/events');

  @override
  Future<bool> requestPermissions() async {
    try {
      // Permission handling is done in the presentation layer with permission_handler
      return true;
    } catch (e) {
      throw ServerException('Failed to request permissions');
    }
  }

  @override
  Future<bool> hasPermissions() async {
    try {
      // Permission checking is done in the presentation layer with permission_handler
      return true;
    } catch (e) {
      throw ServerException('Failed to check permissions');
    }
  }

  @override
  Future<List<Map<String, dynamic>>> getInboxSms({int? limit}) async {
    try {
      final List<dynamic> messages = await _methodChannel.invokeMethod('getInboxSms', {
        'limit': limit ?? 1000,
      });

      return messages.map((message) {
        return {
          // 'address' is the raw numeric phone number
          'address': message['address'] as String? ?? '',
          // 'sender' is an optional resolved contact name (may be same as address)
          'sender': message['sender'] as String? ?? (message['address'] as String? ?? ''),
          'body': message['body'] as String? ?? '',
          'date': message['date'] as int? ?? 0,
        };
      }).toList();
    } catch (e) {
      throw ServerException('Failed to read SMS: ${e.toString()}');
    }
  }

  @override
  Stream<Map<String, dynamic>> listenToIncomingSms() {
    try {
      print('Listening to incoming SMS messages...');
      return _eventChannel.receiveBroadcastStream().map((dynamic message) {
        return {
          'address': message['address'] as String? ?? '',
          'sender': message['sender'] as String? ?? (message['address'] as String? ?? ''),
          'body': message['body'] as String? ?? '',
          'date': message['date'] as int? ?? 0,
        };
      });
    } catch (e) {
      throw ServerException('Failed to listen to SMS: ${e.toString()}');
    }
  }
}
