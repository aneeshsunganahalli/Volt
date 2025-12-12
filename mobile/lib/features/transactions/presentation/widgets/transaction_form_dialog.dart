import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import '../../domain/entities/transaction.dart';
import '../../../../core/theme/app_pallette.dart';
import '../bloc/transaction_event.dart';
import '../bloc/transaction_bloc.dart';
import '../bloc/transaction_state.dart';

class TransactionFormDialog extends StatefulWidget {
  final TransactionEntity? transaction;
  final int userId;
  final Function({
    required int userId,
    required double amount,
    required TransactionType type,
    String? merchant,
    String? category,
    String? upiId,
    String? transactionId,
    DateTime? timestamp,
    double? balance,
    String? bankName,
    String? accountNumber,
    String? rawMessage,
  }) onSubmit;
  const TransactionFormDialog({
    super.key,
    this.transaction,
    required this.userId,
    required this.onSubmit,
  });

  @override
  State<TransactionFormDialog> createState() => _TransactionFormDialogState();
}

class _TransactionFormDialogState extends State<TransactionFormDialog> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _merchantController = TextEditingController();
  final _categoryController = TextEditingController();
  final _upiIdController = TextEditingController();
  final _transactionIdController = TextEditingController();
  final _balanceController = TextEditingController();
  final _bankNameController = TextEditingController();
  final _accountNumberController = TextEditingController();
  final _rawMessageController = TextEditingController();

  TransactionType _selectedType = TransactionType.debit;
  DateTime? _selectedDate;
  File? _selectedImage;
  bool _isScanning = false;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.transaction != null) {
      _populateForm(widget.transaction!);
    }
  }

  void _populateForm(TransactionEntity transaction) {
    _amountController.text = transaction.amount.toString();
    _merchantController.text = transaction.merchant ?? '';
    _categoryController.text = transaction.category ?? '';
    _upiIdController.text = transaction.upiId ?? '';
    _transactionIdController.text = transaction.transactionId ?? '';
    _balanceController.text = transaction.balance?.toString() ?? '';
    _bankNameController.text = transaction.bankName ?? '';
    _accountNumberController.text = transaction.accountNumber ?? '';
    _rawMessageController.text = transaction.rawMessage ?? '';
    _selectedType = transaction.type;
    _selectedDate = transaction.timestamp;
  }

  @override
  void dispose() {
    _amountController.dispose();
    _merchantController.dispose();
    _categoryController.dispose();
    _upiIdController.dispose();
    _transactionIdController.dispose();
    _balanceController.dispose();
    _bankNameController.dispose();
    _accountNumberController.dispose();
    _rawMessageController.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _isScanning = true;
        });

        if (mounted) {
          context.read<TransactionBloc>().add(
                ExtractTransactionFromImageEvent(_selectedImage!),
              );
        }
      }
    }

  Future<void> _pickImageFromGallery() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );

    if (image != null) {
      setState(() {
        _selectedImage = File(image.path);
        _isScanning = true;
      });

      if (mounted) {
        context.read<TransactionBloc>().add(
              ExtractTransactionFromImageEvent(_selectedImage!),
            );
      }
    }
  }

  void _updateFromOCR(TransactionEntity transaction) {
    if (!mounted) {
      debugPrint('Widget not mounted, skipping OCR update');
      return;
    }
    
    try {
      debugPrint('_updateFromOCR called with transaction: amount=${transaction.amount}, merchant=${transaction.merchant}, category=${transaction.category}');
      debugPrint('Before setState - Amount controller text: ${_amountController.text}');
      
      // Clear existing values first
      _amountController.clear();
      _merchantController.clear();
      _categoryController.clear();
      _upiIdController.clear();
      _transactionIdController.clear();
      _balanceController.clear();
      _bankNameController.clear();
      _accountNumberController.clear();
      _rawMessageController.clear();

      // Populate with OCR data
      final amountText = transaction.amount.toString();
      _amountController.text = amountText;
      debugPrint('Set amount controller to: $amountText');
      
      if (transaction.merchant != null && transaction.merchant!.isNotEmpty) {
        _merchantController.text = transaction.merchant!;
        debugPrint('Set merchant controller to: ${transaction.merchant}');
      }
      if (transaction.category != null && transaction.category!.isNotEmpty) {
        _categoryController.text = transaction.category!;
        debugPrint('Set category controller to: ${transaction.category}');
      }
      if (transaction.upiId != null && transaction.upiId!.isNotEmpty) {
        _upiIdController.text = transaction.upiId!;
      }
      if (transaction.transactionId != null && transaction.transactionId!.isNotEmpty) {
        _transactionIdController.text = transaction.transactionId!;
      }
      if (transaction.balance != null) {
        _balanceController.text = transaction.balance!.toString();
      }
      if (transaction.bankName != null && transaction.bankName!.isNotEmpty) {
        _bankNameController.text = transaction.bankName!;
      }
      if (transaction.accountNumber != null && transaction.accountNumber!.isNotEmpty) {
        _accountNumberController.text = transaction.accountNumber!;
      }
      if (transaction.rawMessage != null && transaction.rawMessage!.isNotEmpty) {
        _rawMessageController.text = transaction.rawMessage!;
      }
      
      setState(() {
        _selectedType = transaction.type;
        _selectedDate = transaction.timestamp;
        _isScanning = false;
      });
      
      debugPrint('After setState - Amount controller text: ${_amountController.text}');
      debugPrint('After setState - Merchant controller text: ${_merchantController.text}');
    } catch (e, stackTrace) {
      debugPrint('Error updating form from OCR: $e');
      debugPrint('Stack trace: $stackTrace');
      if (mounted) {
        setState(() {
          _isScanning = false;
        });
      }
    }
  }

  Future<void> _selectDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
    );

    if (picked != null) {
      final TimeOfDay? time = await showTimePicker(
        context: context,
        initialTime: _selectedDate != null
            ? TimeOfDay.fromDateTime(_selectedDate!)
            : TimeOfDay.now(),
      );

      if (time != null) {
        setState(() {
          _selectedDate = DateTime(
            picked.year,
            picked.month,
            picked.day,
            time.hour,
            time.minute,
          );
        });
      }
    }
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      widget.onSubmit(
        userId: widget.userId,
        amount: double.parse(_amountController.text),
        type: _selectedType,
        merchant: _merchantController.text.isEmpty
            ? null
            : _merchantController.text.trim(),
        category: _categoryController.text.isEmpty
            ? null
            : _categoryController.text.trim(),
        upiId: _upiIdController.text.isEmpty
            ? null
            : _upiIdController.text.trim(),
        transactionId: _transactionIdController.text.isEmpty
            ? null
            : _transactionIdController.text.trim(),
        timestamp: _selectedDate,
        balance: _balanceController.text.isEmpty
            ? null
            : double.tryParse(_balanceController.text),
        bankName: _bankNameController.text.isEmpty
            ? null
            : _bankNameController.text.trim(),
        accountNumber: _accountNumberController.text.isEmpty
            ? null
            : _accountNumberController.text.trim(),
        rawMessage: _rawMessageController.text.isEmpty
            ? null
            : _rawMessageController.text.trim(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEdit = widget.transaction != null;

    return BlocListener<TransactionBloc, TransactionState>(
      listener: (context, state) {
        debugPrint('BlocListener received state: ${state.runtimeType}');
        if (state is TransactionExtractedFromImage) {
          debugPrint('OCR extraction successful: amount=${state.transaction.amount}, merchant=${state.transaction.merchant}, category=${state.transaction.category}');
          debugPrint('Transaction type: ${state.transaction.type}');
          debugPrint('Transaction timestamp: ${state.transaction.timestamp}');
          _updateFromOCR(state.transaction);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: const Text('Bill scanned successfully! Please review the fields.'),
                backgroundColor: ColorPalette.success,
                behavior: SnackBarBehavior.floating,
              ),
            );
          }
        } else if (state is TransactionError && _isScanning) {
          setState(() {
            _isScanning = false;
          });
          debugPrint('OCR Error: ${state.message}');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('OCR Error: ${state.message}'),
              backgroundColor: ColorPalette.warning,
              behavior: SnackBarBehavior.floating,
            ),
          );
        } else if (state is TransactionCreated || state is TransactionUpdated) {
          setState(() {
            _isLoading = false;
          });
        } else if (state is TransactionError && _isLoading) {
          setState(() {
            _isLoading = false;
          });
        }
      },
      child: _buildDialog(context, theme, isEdit),
    );
  }

  Widget _buildDialog(BuildContext context, ThemeData theme, bool isEdit) {

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(16),
      child: Container(
        constraints: const BoxConstraints(maxHeight: 700),
        decoration: BoxDecoration(
          color: ColorPalette.gray900,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: ColorPalette.gray700,
            width: 1.5,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: ColorPalette.gray700,
                    width: 1,
                  ),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    isEdit ? Icons.edit_rounded : Icons.add_rounded,
                    color: ColorPalette.textPrimaryDark,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      isEdit ? 'Edit Transaction' : 'Add Transaction',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: ColorPalette.textPrimaryDark,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: Icon(
                      Icons.close_rounded,
                      color: ColorPalette.textSecondaryDark,
                    ),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            // Form Content
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // OCR Scan Section
                      if (!isEdit) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: ColorPalette.gray800,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: ColorPalette.gray700,
                              width: 1,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    Icons.document_scanner_rounded,
                                    color: theme.colorScheme.primary,
                                    size: 20,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Scan Bill',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: ColorPalette.textPrimaryDark,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              if (_selectedImage != null) ...[
                                Container(
                                  height: 120,
                                  width: double.infinity,
                                  decoration: BoxDecoration(
                                    color: ColorPalette.gray900,
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(
                                      color: ColorPalette.gray700,
                                    ),
                                  ),
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(8),
                                    child: Image.file(
                                      _selectedImage!,
                                      fit: BoxFit.cover,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 12),
                              ],
                              Row(
                                children: [
                                  Expanded(
                                    child: OutlinedButton.icon(
                                      onPressed: _isScanning
                                          ? null
                                          : _pickImage,
                                      icon: Icon(
                                        Icons.camera_alt_rounded,
                                        size: 18,
                                      ),
                                      label: const Text('Camera'),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor:
                                            ColorPalette.textPrimaryDark,
                                        side: BorderSide(
                                          color: ColorPalette.gray700,
                                        ),
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 12,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: OutlinedButton.icon(
                                      onPressed: _isScanning
                                          ? null
                                          : _pickImageFromGallery,
                                      icon: Icon(
                                        Icons.photo_library_rounded,
                                        size: 18,
                                      ),
                                      label: const Text('Gallery'),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor:
                                            ColorPalette.textPrimaryDark,
                                        side: BorderSide(
                                          color: ColorPalette.gray700,
                                        ),
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 12,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              if (_isScanning) ...[
                                const SizedBox(height: 12),
                                Row(
                                  children: [
                                    SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor: AlwaysStoppedAnimation<Color>(
                                          theme.colorScheme.primary,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Text(
                                      'Scanning bill...',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: ColorPalette.textSecondaryDark,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                      // Transaction Type
                      Text(
                        'Transaction Type',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: ColorPalette.textPrimaryDark,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTypeChip(
                              'Debit',
                              TransactionType.debit,
                              ColorPalette.error,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildTypeChip(
                              'Credit',
                              TransactionType.credit,
                              ColorPalette.success,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      // Amount
                      _buildTextField(
                        controller: _amountController,
                        label: 'Amount *',
                        hint: '0.00',
                        keyboardType: TextInputType.number,
                        prefixIcon: Icons.attach_money_rounded,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter amount';
                          }
                          if (double.tryParse(value) == null ||
                              double.parse(value) <= 0) {
                            return 'Please enter a valid amount';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      // Merchant
                      _buildTextField(
                        controller: _merchantController,
                        label: 'Merchant',
                        hint: 'Merchant name',
                        prefixIcon: Icons.store_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Category
                      _buildTextField(
                        controller: _categoryController,
                        label: 'Category',
                        hint: 'e.g., FOOD, SHOPPING',
                        prefixIcon: Icons.category_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Date & Time
                      Text(
                        'Date & Time',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: ColorPalette.textPrimaryDark,
                        ),
                      ),
                      const SizedBox(height: 8),
                      InkWell(
                        onTap: _selectDate,
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: ColorPalette.gray800,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: ColorPalette.gray700,
                              width: 1,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.calendar_today_rounded,
                                color: ColorPalette.textSecondaryDark,
                                size: 20,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _selectedDate != null
                                      ? '${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year} ${_selectedDate!.hour.toString().padLeft(2, '0')}:${_selectedDate!.minute.toString().padLeft(2, '0')}'
                                      : 'Select date and time',
                                  style: TextStyle(
                                    fontSize: 16,
                                    color: _selectedDate != null
                                        ? ColorPalette.textPrimaryDark
                                        : ColorPalette.textSecondaryDark,
                                  ),
                                ),
                              ),
                              Icon(
                                Icons.arrow_forward_ios_rounded,
                                color: ColorPalette.textSecondaryDark,
                                size: 16,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      // UPI ID
                      _buildTextField(
                        controller: _upiIdController,
                        label: 'UPI ID',
                        hint: 'UPI ID',
                        prefixIcon: Icons.account_circle_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Transaction ID
                      _buildTextField(
                        controller: _transactionIdController,
                        label: 'Transaction ID',
                        hint: 'Transaction reference ID',
                        prefixIcon: Icons.tag_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Balance
                      _buildTextField(
                        controller: _balanceController,
                        label: 'Balance',
                        hint: 'Account balance',
                        keyboardType: TextInputType.number,
                        prefixIcon: Icons.account_balance_wallet_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Bank Name
                      _buildTextField(
                        controller: _bankNameController,
                        label: 'Bank Name',
                        hint: 'Bank name',
                        prefixIcon: Icons.account_balance_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Account Number
                      _buildTextField(
                        controller: _accountNumberController,
                        label: 'Account Number',
                        hint: 'Account number',
                        prefixIcon: Icons.credit_card_rounded,
                      ),
                      const SizedBox(height: 16),
                      // Raw Message
                      _buildTextField(
                        controller: _rawMessageController,
                        label: 'Raw Message',
                        hint: 'Original transaction message',
                        prefixIcon: Icons.message_rounded,
                        maxLines: 3,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            // Footer Actions
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(
                    color: ColorPalette.gray700,
                    width: 1,
                  ),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _isLoading
                          ? null
                          : () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: ColorPalette.textPrimaryDark,
                        side: BorderSide(color: ColorPalette.gray700),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text('Cancel'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _submitForm,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: theme.colorScheme.primary,
                        foregroundColor: theme.colorScheme.onPrimary,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: 0,
                      ),
                      child: _isLoading
                          ? SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(
                                  theme.colorScheme.onPrimary,
                                ),
                              ),
                            )
                          : Text(isEdit ? 'Update' : 'Add Transaction'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypeChip(String label, TransactionType type, Color color) {
    final isSelected = _selectedType == type;
    return InkWell(
      onTap: () {
        setState(() {
          _selectedType = type;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: isSelected
              ? color.withOpacity(0.2)
              : ColorPalette.gray800,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? color : ColorPalette.gray700,
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              type == TransactionType.credit
                  ? Icons.arrow_downward_rounded
                  : Icons.arrow_upward_rounded,
              color: isSelected ? color : ColorPalette.textSecondaryDark,
              size: 18,
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 16,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                color: isSelected
                    ? color
                    : ColorPalette.textSecondaryDark,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData prefixIcon,
    TextInputType? keyboardType,
    int maxLines = 1,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: ColorPalette.textPrimaryDark,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          maxLines: maxLines,
          validator: validator,
          style: TextStyle(
            color: ColorPalette.textPrimaryDark,
            fontSize: 16,
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
              color: ColorPalette.textSecondaryDark,
            ),
            prefixIcon: Icon(
              prefixIcon,
              color: ColorPalette.textSecondaryDark,
              size: 20,
            ),
            filled: true,
            fillColor: ColorPalette.gray800,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: ColorPalette.gray700,
                width: 1,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: ColorPalette.gray700,
                width: 1,
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: Theme.of(context).colorScheme.primary,
                width: 1.5,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: ColorPalette.error,
                width: 1,
              ),
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 16,
            ),
          ),
        ),
      ],
    );
  }
}

