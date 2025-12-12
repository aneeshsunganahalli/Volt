import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../init_dependencies.dart';
import '../../../../core/theme/app_pallette.dart';
import '../../../../features/auth/data/datasources/auth_local_data_source.dart';
import '../bloc/lean_week_bloc.dart';
import '../bloc/lean_week_event.dart';
import '../bloc/lean_week_state.dart';

class LeanWeekPage extends StatefulWidget {
  const LeanWeekPage({super.key});

  @override
  State<LeanWeekPage> createState() => _LeanWeekPageState();
}

class _LeanWeekPageState extends State<LeanWeekPage>
    with SingleTickerProviderStateMixin {
  String? _token;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadToken();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadToken() async {
    final authLocalDataSource = sl<AuthLocalDataSource>();
    final token = await authLocalDataSource.getToken();
    setState(() {
      _token = token;
    });
    if (_token != null) {
      _loadAnalysis();
    }
  }

  void _loadAnalysis() {
    if (_token == null) return;
    context.read<LeanWeekBloc>().add(
          GetLeanWeekAnalysisEvent(token: _token!),
        );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: theme.scaffoldBackgroundColor,
        elevation: 0,
        title: Text(
          'Lean Week Analysis',
          style: TextStyle(
            color: theme.colorScheme.onSurface,
            fontWeight: FontWeight.w600,
          ),
        ),
        bottom: TabBar(
          controller: _tabController,
          onTap: (index) {
            if (_token != null) {
              switch (index) {
                case 0:
                  _loadAnalysis();
                  break;
                case 1:
                  context.read<LeanWeekBloc>().add(
                        GetCashFlowForecastEvent(token: _token!),
                      );
                  break;
                case 2:
                  context.read<LeanWeekBloc>().add(
                        GetIncomeSmoothingRecommendationsEvent(token: _token!),
                      );
                  break;
              }
            }
          },
          tabs: const [
            Tab(text: 'Overview', icon: Icon(Icons.dashboard)),
            Tab(text: 'Forecast', icon: Icon(Icons.trending_up)),
            Tab(text: 'Recommendations', icon: Icon(Icons.lightbulb)),
          ],
        ),
      ),
      body: BlocConsumer<LeanWeekBloc, LeanWeekState>(
        listener: (context, state) {
          if (state is LeanWeekError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: theme.colorScheme.error,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is LeanWeekLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is LeanWeekAnalysisLoaded) {
            return _buildOverviewTab(context, state.analysis);
          }

          if (state is CashFlowForecastLoaded) {
            return _buildForecastTab(context, state.forecast);
          }

          if (state is IncomeSmoothingRecommendationsLoaded) {
            return _buildRecommendationsTab(context, state.recommendations);
          }

          if (state is LeanWeekError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 64,
                    color: theme.colorScheme.error,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    state.message,
                    style: TextStyle(color: theme.colorScheme.error),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _loadAnalysis,
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.analytics_outlined,
                  size: 64,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(height: 16),
                Text(
                  'Tap to load analysis',
                  style: TextStyle(color: theme.colorScheme.onSurface),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: _loadAnalysis,
                  child: const Text('Load Analysis'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildOverviewTab(BuildContext context, analysis) {
    final theme = Theme.of(context);
    final summary = analysis.summary;
    final riskColor = _getRiskColor(summary.riskLevel);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Risk Summary Card
          Card(
            color: riskColor.withOpacity(0.1),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        _getRiskIcon(summary.riskLevel),
                        color: riskColor,
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Risk Level: ${summary.riskLevel}',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: riskColor,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              summary.riskMessage,
                              style: TextStyle(
                                color: theme.colorScheme.onSurface,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  if (summary.immediateActionNeeded) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: ColorPalette.errorLight,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.warning, color: ColorPalette.error),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Immediate action required',
                              style: TextStyle(
                                color: ColorPalette.error,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Historical Analysis
          Text(
            'Historical Analysis',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  context,
                  'Lean Frequency',
                  '${(analysis.historicalAnalysis.monthly.leanFrequency * 100).toStringAsFixed(1)}%',
                  Icons.trending_down,
                  ColorPalette.warning,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  context,
                  'Avg Severity',
                  '₹${analysis.historicalAnalysis.monthly.avgLeanSeverity.toStringAsFixed(2)}',
                  Icons.attach_money,
                  ColorPalette.error,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Cash Flow Forecast Summary
          Text(
            'Forecast Summary',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildForecastRow(
                    context,
                    'Avg Monthly Income',
                    '₹${analysis.cashFlowForecast.avgMonthlyIncome.toStringAsFixed(2)}',
                  ),
                  const Divider(),
                  _buildForecastRow(
                    context,
                    'Avg Monthly Expenses',
                    '₹${analysis.cashFlowForecast.avgMonthlyExpenses.toStringAsFixed(2)}',
                  ),
                  const Divider(),
                  _buildForecastRow(
                    context,
                    'Income Volatility',
                    '${(analysis.cashFlowForecast.incomeVolatility * 100).toStringAsFixed(1)}%',
                  ),
                  const Divider(),
                  _buildForecastRow(
                    context,
                    'Confidence',
                    '${(analysis.cashFlowForecast.confidence * 100).toStringAsFixed(1)}%',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Warnings
          if (analysis.cashFlowForecast.warnings.isNotEmpty) ...[
            Text(
              'Warnings',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 12),
            ...analysis.cashFlowForecast.warnings.map((warning) => Card(
                  color: ColorPalette.warningLight,
                  child: ListTile(
                    leading: const Icon(Icons.warning, color: ColorPalette.warning),
                    title: Text(warning),
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildForecastTab(BuildContext context, forecast) {
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary Cards
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  context,
                  'Avg Income',
                  '₹${forecast.avgMonthlyIncome.toStringAsFixed(2)}',
                  Icons.arrow_upward,
                  ColorPalette.success,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  context,
                  'Avg Expenses',
                  '₹${forecast.avgMonthlyExpenses.toStringAsFixed(2)}',
                  Icons.arrow_downward,
                  ColorPalette.error,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  context,
                  'Volatility',
                  '${(forecast.incomeVolatility * 100).toStringAsFixed(1)}%',
                  Icons.show_chart,
                  ColorPalette.warning,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  context,
                  'Confidence',
                  '${(forecast.confidence * 100).toStringAsFixed(1)}%',
                  Icons.verified,
                  ColorPalette.info,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Forecast Periods
          Text(
            'Monthly Forecasts',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 12),
          ...forecast.forecasts.map((period) => _buildForecastPeriodCard(
                context,
                period,
              )),
          const SizedBox(height: 16),

          // Warnings
          if (forecast.warnings.isNotEmpty) ...[
            Text(
              'Warnings',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 12),
            ...forecast.warnings.map((warning) => Card(
                  color: ColorPalette.warningLight,
                  child: ListTile(
                    leading: const Icon(Icons.warning, color: ColorPalette.warning),
                    title: Text(warning),
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildRecommendationsTab(BuildContext context, recommendations) {
    final theme = Theme.of(context);
    final strategy = recommendations.strategy;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Emergency Fund Card
          Card(
            color: ColorPalette.infoLight,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.savings, color: ColorPalette.info, size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Emergency Fund',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: theme.colorScheme.onSurface,
                              ),
                            ),
                            Text(
                              'Target: ₹${recommendations.targetEmergencyFund.toStringAsFixed(2)}',
                              style: TextStyle(
                                color: theme.colorScheme.onSurface,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  LinearProgressIndicator(
                    value: recommendations.currentBalance /
                        recommendations.targetEmergencyFund,
                    backgroundColor: Colors.grey[300],
                    valueColor: const AlwaysStoppedAnimation<Color>(ColorPalette.info),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Current: ₹${recommendations.currentBalance.toStringAsFixed(2)}',
                        style: TextStyle(
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                      Text(
                        'Gap: ₹${recommendations.emergencyFundGap.toStringAsFixed(2)}',
                        style: TextStyle(
                          color: ColorPalette.warning,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Savings Recommendation
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Savings Recommendation',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildRecommendationRow(
                    context,
                    'Monthly Save Amount',
                    '₹${recommendations.monthlySaveAmount.toStringAsFixed(2)}',
                  ),
                  const Divider(),
                  _buildRecommendationRow(
                    context,
                    'Save Rate',
                    '${(recommendations.recommendedSaveRate * 100).toStringAsFixed(1)}%',
                  ),
                  if (recommendations.monthsToTarget != null) ...[
                    const Divider(),
                    _buildRecommendationRow(
                      context,
                      'Months to Target',
                      '${recommendations.monthsToTarget!.toStringAsFixed(1)} months',
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Strategy
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Strategy',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Chip(
                    label: Text(
                      'Volatility: ${strategy.volatilityLevel.toUpperCase()}',
                    ),
                    backgroundColor: _getVolatilityColor(strategy.volatilityLevel),
                  ),
                  const SizedBox(height: 12),
                  if (strategy.recommendations.isNotEmpty) ...[
                    Text(
                      'Recommendations',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...strategy.recommendations.map((rec) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.check_circle,
                                  color: ColorPalette.success, size: 20),
                              const SizedBox(width: 8),
                              Expanded(child: Text(rec)),
                            ],
                          ),
                        )),
                  ],
                  if (strategy.actionItems.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text(
                      'Action Items',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...strategy.actionItems.map((item) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.play_arrow,
                                  color: ColorPalette.info, size: 20),
                              const SizedBox(width: 8),
                              Expanded(child: Text(item)),
                            ],
                          ),
                        )),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildForecastRow(BuildContext context, String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
      ],
    );
  }

  Widget _buildForecastPeriodCard(BuildContext context, period) {
    final theme = Theme.of(context);
    final isLean = period.isLeanPeriod;
    final isRisk = period.balanceAtRisk;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: isRisk
          ? ColorPalette.errorLight
          : isLean
              ? ColorPalette.warningLight
              : null,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Month ${period.period}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                if (isLean)
                  Chip(
                    label: const Text('Lean Period'),
                    backgroundColor: ColorPalette.warningLight,
                  ),
                if (isRisk)
                  Chip(
                    label: const Text('At Risk'),
                    backgroundColor: ColorPalette.errorLight,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            _buildScenarioRow('Best', period.netCashFlow.best, ColorPalette.success),
            _buildScenarioRow('Likely', period.netCashFlow.likely, ColorPalette.info),
            _buildScenarioRow('Worst', period.netCashFlow.worst, ColorPalette.error),
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioRow(String label, double value, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
          Text(
            '₹${value.toStringAsFixed(2)}',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationRow(
      BuildContext context, String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurface,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.primary,
          ),
        ),
      ],
    );
  }

  Color _getRiskColor(String riskLevel) {
    switch (riskLevel.toUpperCase()) {
      case 'LOW':
        return ColorPalette.success;
      case 'MODERATE':
        return ColorPalette.warning;
      case 'HIGH':
        return ColorPalette.error;
      default:
        return Colors.grey;
    }
  }

  IconData _getRiskIcon(String riskLevel) {
    switch (riskLevel.toUpperCase()) {
      case 'LOW':
        return Icons.check_circle;
      case 'MODERATE':
        return Icons.warning;
      case 'HIGH':
        return Icons.error;
      default:
        return Icons.help;
    }
  }

  Color _getVolatilityColor(String level) {
    switch (level.toLowerCase()) {
      case 'low':
        return ColorPalette.successLight;
      case 'medium':
        return ColorPalette.warningLight;
      case 'high':
        return ColorPalette.errorLight;
      default:
        return Colors.grey.withOpacity(0.2);
    }
  }
}

