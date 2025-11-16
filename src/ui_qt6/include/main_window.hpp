/**
 * @file main_window.hpp
 * @brief Modern Qt6 main window with animations and dashboard
 */

#ifndef COPILOT_MAIN_WINDOW_HPP
#define COPILOT_MAIN_WINDOW_HPP

#include <QMainWindow>
#include <QSystemTrayIcon>
#include <QPropertyAnimation>
#include <QGraphicsOpacityEffect>
#include <QTimer>
#include <memory>

namespace Ui {
class MainWindow;
}

namespace copilot {
namespace ui {

/**
 * @brief Main application window with modern UI
 *
 * Features:
 * - Dashboard for plugins and system status
 * - Animated transitions and effects
 * - System tray integration
 * - Quick access toolbar
 * - Real-time event monitoring
 */
class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget* parent = nullptr);
    ~MainWindow() override;

    /**
     * @brief Show dashboard with animation
     */
    void showDashboard();

    /**
     * @brief Hide to tray with animation
     */
    void hideToTray();

    /**
     * @brief Show notification
     * @param title Notification title
     * @param message Notification message
     * @param duration_ms Duration in milliseconds
     */
    void showNotification(const QString& title,
                         const QString& message,
                         int duration_ms = 3000);

    /**
     * @brief Update plugin list
     */
    void updatePluginList();

    /**
     * @brief Update system status
     */
    void updateSystemStatus();

signals:
    /**
     * @brief Emitted when user requests plugin load
     */
    void pluginLoadRequested(const QString& plugin_path);

    /**
     * @brief Emitted when user requests plugin unload
     */
    void pluginUnloadRequested(const QString& plugin_id);

    /**
     * @brief Emitted when AI model selection changes
     */
    void aiModelChanged(const QString& model_name);

    /**
     * @brief Emitted when user triggers screenshot
     */
    void screenshotRequested();

    /**
     * @brief Emitted when user triggers window arrangement
     */
    void windowArrangementRequested(const QString& layout);

protected:
    void closeEvent(QCloseEvent* event) override;
    void showEvent(QShowEvent* event) override;
    void hideEvent(QHideEvent* event) override;

private slots:
    void on_tray_activated(QSystemTrayIcon::ActivationReason reason);
    void on_plugin_load_clicked();
    void on_plugin_unload_clicked();
    void on_ai_model_selected(const QString& model);
    void on_screenshot_clicked();
    void on_settings_clicked();
    void on_about_clicked();

private:
    void setupUi();
    void setupTrayIcon();
    void setupAnimations();
    void setupConnections();

    // Animations
    void animateShow();
    void animateHide();
    void animatePanelSwitch(QWidget* from, QWidget* to);

    // UI components
    std::unique_ptr<Ui::MainWindow> ui_;
    QSystemTrayIcon* tray_icon_;
    QMenu* tray_menu_;

    // Animations
    QPropertyAnimation* window_animation_;
    QPropertyAnimation* opacity_animation_;

    // State
    bool is_hidden_to_tray_;
    QPoint last_window_pos_;
};

} // namespace ui
} // namespace copilot

#endif // COPILOT_MAIN_WINDOW_HPP
