/**
 * @file dashboard_widget.hpp
 * @brief Dashboard widget with plugin management and system overview
 */

#ifndef COPILOT_DASHBOARD_WIDGET_HPP
#define COPILOT_DASHBOARD_WIDGET_HPP

#include <QWidget>
#include <QListWidget>
#include <QTableWidget>
#include <QComboBox>
#include <QPushButton>
#include <QLabel>
#include <QProgressBar>
#include <QTimer>
#include <vector>
#include <memory>

namespace copilot {
namespace ui {

/**
 * @brief Plugin information structure
 */
struct PluginInfo {
    QString id;
    QString name;
    QString version;
    QString author;
    QString description;
    bool is_enabled;
    bool is_loaded;
    uint32_t capabilities;
};

/**
 * @brief System status information
 */
struct SystemStatus {
    double cpu_usage;
    double memory_usage;
    size_t active_windows;
    size_t running_plugins;
    size_t pending_events;
    QString current_ai_model;
};

/**
 * @brief Dashboard widget for copilot control
 *
 * Features:
 * - Plugin list with enable/disable controls
 * - System status monitoring
 * - AI model selection
 * - Quick actions
 * - Event log
 */
class DashboardWidget : public QWidget {
    Q_OBJECT

public:
    explicit DashboardWidget(QWidget* parent = nullptr);
    ~DashboardWidget() override;

    /**
     * @brief Update plugin list
     */
    void updatePlugins(const std::vector<PluginInfo>& plugins);

    /**
     * @brief Update system status
     */
    void updateSystemStatus(const SystemStatus& status);

    /**
     * @brief Add event to log
     */
    void addEventLog(const QString& event_type,
                    const QString& message,
                    const QString& timestamp);

signals:
    void loadPluginClicked();
    void unloadPluginClicked(const QString& plugin_id);
    void enablePluginClicked(const QString& plugin_id, bool enable);
    void aiModelSelected(const QString& model);
    void quickActionTriggered(const QString& action);

private slots:
    void on_plugin_item_clicked(QListWidgetItem* item);
    void on_load_plugin_btn_clicked();
    void on_unload_plugin_btn_clicked();
    void on_ai_model_combo_changed(int index);
    void on_quick_action_clicked();
    void on_refresh_status();

private:
    void setupUi();
    void setupPluginPanel();
    void setupStatusPanel();
    void setupAiPanel();
    void setupQuickActions();
    void setupEventLog();

    // UI components
    QListWidget* plugin_list_;
    QPushButton* load_plugin_btn_;
    QPushButton* unload_plugin_btn_;

    QLabel* cpu_label_;
    QProgressBar* cpu_progress_;
    QLabel* memory_label_;
    QProgressBar* memory_progress_;
    QLabel* windows_label_;
    QLabel* events_label_;

    QComboBox* ai_model_combo_;
    QPushButton* configure_ai_btn_;

    QTableWidget* event_log_;

    // Quick action buttons
    QPushButton* screenshot_btn_;
    QPushButton* window_arrange_btn_;
    QPushButton* macro_record_btn_;

    // Update timer
    QTimer* status_timer_;

    // Current selection
    QString selected_plugin_id_;
};

} // namespace ui
} // namespace copilot

#endif // COPILOT_DASHBOARD_WIDGET_HPP
