/**
 * @file main_window.cpp
 * @brief Implementation of main window
 */

#include "main_window.hpp"
#include "dashboard_widget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QMenuBar>
#include <QStatusBar>
#include <QCloseEvent>
#include <QShowEvent>
#include <QHideEvent>
#include <QApplication>
#include <QStyle>
#include <QScreen>
#include <QMessageBox>

namespace copilot {
namespace ui {

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
    , tray_icon_(nullptr)
    , tray_menu_(nullptr)
    , window_animation_(nullptr)
    , opacity_animation_(nullptr)
    , is_hidden_to_tray_(false)
{
    setupUi();
    setupTrayIcon();
    setupAnimations();
    setupConnections();

    // Set window properties
    setWindowTitle("Linux Copilot");
    resize(1200, 800);

    // Center window
    QScreen* screen = QApplication::primaryScreen();
    QRect screen_geometry = screen->availableGeometry();
    int x = (screen_geometry.width() - width()) / 2;
    int y = (screen_geometry.height() - height()) / 2;
    move(x, y);
}

MainWindow::~MainWindow() {
    delete tray_icon_;
    delete tray_menu_;
}

void MainWindow::setupUi() {
    // Create central widget
    QWidget* central = new QWidget(this);
    setCentralWidget(central);

    // Create main layout
    QVBoxLayout* main_layout = new QVBoxLayout(central);

    // Create dashboard
    DashboardWidget* dashboard = new DashboardWidget(this);
    main_layout->addWidget(dashboard);

    // Create menu bar
    QMenuBar* menu_bar = menuBar();

    // File menu
    QMenu* file_menu = menu_bar->addMenu("&File");
    file_menu->addAction("&Settings", this, &MainWindow::on_settings_clicked);
    file_menu->addSeparator();
    file_menu->addAction("&Quit", qApp, &QApplication::quit);

    // Plugins menu
    QMenu* plugins_menu = menu_bar->addMenu("&Plugins");
    plugins_menu->addAction("&Load Plugin...", this, &MainWindow::on_plugin_load_clicked);
    plugins_menu->addAction("&Unload Plugin", this, &MainWindow::on_plugin_unload_clicked);
    plugins_menu->addSeparator();
    plugins_menu->addAction("&Refresh", this, &MainWindow::updatePluginList);

    // Tools menu
    QMenu* tools_menu = menu_bar->addMenu("&Tools");
    tools_menu->addAction("&Screenshot", this, &MainWindow::on_screenshot_clicked);
    tools_menu->addAction("&Window Arrangement", []() {
        // Emit signal
    });

    // Help menu
    QMenu* help_menu = menu_bar->addMenu("&Help");
    help_menu->addAction("&About", this, &MainWindow::on_about_clicked);
    help_menu->addAction("&Documentation", []() {
        // Open documentation
    });

    // Status bar
    statusBar()->showMessage("Ready");

    // Apply modern stylesheet
    setStyleSheet(R"(
        QMainWindow {
            background-color: #1e1e1e;
        }
        QMenuBar {
            background-color: #2d2d30;
            color: #ffffff;
            border-bottom: 1px solid #3e3e42;
        }
        QMenuBar::item:selected {
            background-color: #3e3e42;
        }
        QMenu {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }
        QMenu::item:selected {
            background-color: #094771;
        }
        QStatusBar {
            background-color: #007acc;
            color: #ffffff;
        }
    )");
}

void MainWindow::setupTrayIcon() {
    // Create tray icon
    tray_icon_ = new QSystemTrayIcon(this);
    tray_icon_->setIcon(QIcon::fromTheme("applications-system"));
    tray_icon_->setToolTip("Linux Copilot");

    // Create tray menu
    tray_menu_ = new QMenu(this);
    tray_menu_->addAction("Show Dashboard", this, &MainWindow::showDashboard);
    tray_menu_->addSeparator();
    tray_menu_->addAction("Screenshot", this, &MainWindow::on_screenshot_clicked);
    tray_menu_->addSeparator();
    tray_menu_->addAction("Quit", qApp, &QApplication::quit);

    tray_icon_->setContextMenu(tray_menu_);
    tray_icon_->show();

    // Connect signals
    connect(tray_icon_, &QSystemTrayIcon::activated,
            this, &MainWindow::on_tray_activated);
}

void MainWindow::setupAnimations() {
    // Window fade animation
    QGraphicsOpacityEffect* opacity_effect = new QGraphicsOpacityEffect(this);
    setGraphicsEffect(opacity_effect);

    opacity_animation_ = new QPropertyAnimation(opacity_effect, "opacity", this);
    opacity_animation_->setDuration(300);
    opacity_animation_->setStartValue(0.0);
    opacity_animation_->setEndValue(1.0);
    opacity_animation_->setEasingCurve(QEasingCurve::InOutQuad);

    // Window geometry animation
    window_animation_ = new QPropertyAnimation(this, "geometry", this);
    window_animation_->setDuration(300);
    window_animation_->setEasingCurve(QEasingCurve::InOutQuad);
}

void MainWindow::setupConnections() {
    // Connect dashboard signals
    DashboardWidget* dashboard = findChild<DashboardWidget*>();
    if (dashboard) {
        connect(dashboard, &DashboardWidget::loadPluginClicked,
                this, &MainWindow::on_plugin_load_clicked);
        connect(dashboard, &DashboardWidget::aiModelSelected,
                this, &MainWindow::on_ai_model_selected);
    }
}

void MainWindow::showDashboard() {
    if (is_hidden_to_tray_) {
        animateShow();
        is_hidden_to_tray_ = false;
    }
    show();
    raise();
    activateWindow();
}

void MainWindow::hideToTray() {
    if (!is_hidden_to_tray_) {
        animateHide();
        is_hidden_to_tray_ = true;
    }
}

void MainWindow::showNotification(const QString& title,
                                  const QString& message,
                                  int duration_ms) {
    if (tray_icon_) {
        tray_icon_->showMessage(title, message,
                               QSystemTrayIcon::Information,
                               duration_ms);
    }
}

void MainWindow::updatePluginList() {
    DashboardWidget* dashboard = findChild<DashboardWidget*>();
    if (dashboard) {
        // This would be called with actual plugin data
        // dashboard->updatePlugins(plugins);
    }
}

void MainWindow::updateSystemStatus() {
    DashboardWidget* dashboard = findChild<DashboardWidget*>();
    if (dashboard) {
        // This would be called with actual status data
        // dashboard->updateSystemStatus(status);
    }
}

void MainWindow::closeEvent(QCloseEvent* event) {
    if (tray_icon_ && tray_icon_->isVisible()) {
        hide();
        event->ignore();
        showNotification("Linux Copilot",
                        "Application minimized to tray",
                        2000);
    } else {
        event->accept();
    }
}

void MainWindow::showEvent(QShowEvent* event) {
    QMainWindow::showEvent(event);
    animateShow();
}

void MainWindow::hideEvent(QHideEvent* event) {
    QMainWindow::hideEvent(event);
}

void MainWindow::on_tray_activated(QSystemTrayIcon::ActivationReason reason) {
    if (reason == QSystemTrayIcon::Trigger ||
        reason == QSystemTrayIcon::DoubleClick) {
        if (isVisible()) {
            hideToTray();
        } else {
            showDashboard();
        }
    }
}

void MainWindow::on_plugin_load_clicked() {
    emit pluginLoadRequested("");
}

void MainWindow::on_plugin_unload_clicked() {
    emit pluginUnloadRequested("");
}

void MainWindow::on_ai_model_selected(const QString& model) {
    emit aiModelChanged(model);
    statusBar()->showMessage("AI Model: " + model);
}

void MainWindow::on_screenshot_clicked() {
    emit screenshotRequested();
}

void MainWindow::on_settings_clicked() {
    // Open settings dialog
}

void MainWindow::on_about_clicked() {
    QMessageBox::about(this, "About Linux Copilot",
        "<h2>Linux Copilot v1.0</h2>"
        "<p>High-performance, visual, modular system-level automation framework</p>"
        "<p>Built with Qt6 and C++17</p>"
        "<p>Copyright © 2024</p>");
}

void MainWindow::animateShow() {
    opacity_animation_->setDirection(QPropertyAnimation::Forward);
    opacity_animation_->start();
}

void MainWindow::animateHide() {
    opacity_animation_->setDirection(QPropertyAnimation::Backward);
    opacity_animation_->start();

    // Hide window after animation completes
    connect(opacity_animation_, &QPropertyAnimation::finished,
            this, &QWidget::hide, Qt::UniqueConnection);
}

void MainWindow::animatePanelSwitch(QWidget* from, QWidget* to) {
    // Fade out current panel
    QGraphicsOpacityEffect* from_effect = new QGraphicsOpacityEffect(from);
    from->setGraphicsEffect(from_effect);

    QPropertyAnimation* from_anim = new QPropertyAnimation(from_effect, "opacity");
    from_anim->setDuration(200);
    from_anim->setStartValue(1.0);
    from_anim->setEndValue(0.0);

    // Fade in new panel
    QGraphicsOpacityEffect* to_effect = new QGraphicsOpacityEffect(to);
    to->setGraphicsEffect(to_effect);

    QPropertyAnimation* to_anim = new QPropertyAnimation(to_effect, "opacity");
    to_anim->setDuration(200);
    to_anim->setStartValue(0.0);
    to_anim->setEndValue(1.0);

    // Start animations
    from_anim->start(QPropertyAnimation::DeleteWhenStopped);

    connect(from_anim, &QPropertyAnimation::finished, [to_anim, to, from]() {
        from->hide();
        to->show();
        to_anim->start(QPropertyAnimation::DeleteWhenStopped);
    });
}

} // namespace ui
} // namespace copilot
