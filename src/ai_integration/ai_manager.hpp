/**
 * @file ai_manager.hpp
 * @brief AI model integration manager for LLaMA, GPT, and other models
 */

#ifndef COPILOT_AI_MANAGER_HPP
#define COPILOT_AI_MANAGER_HPP

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <unordered_map>
#include <mutex>

namespace copilot {
namespace ai {

/**
 * @brief AI model types
 */
enum class AIModelType {
    LLAMA,
    LLAMA2,
    GPT3_5,
    GPT4,
    MISTRAL,
    CUSTOM
};

/**
 * @brief AI model configuration
 */
struct AIModelConfig {
    AIModelType type;
    std::string name;
    std::string model_path;          // Path to model file or API endpoint
    std::string api_key;              // API key for cloud models
    size_t context_length;            // Maximum context length
    size_t max_tokens;                // Maximum tokens to generate
    float temperature;                // Sampling temperature
    float top_p;                      // Nucleus sampling parameter
    bool use_gpu;                     // Use GPU acceleration
    size_t gpu_layers;                // Number of GPU layers (for local models)
    std::string system_prompt;        // System prompt
};

/**
 * @brief AI inference request
 */
struct AIRequest {
    std::string prompt;
    size_t max_tokens;
    float temperature;
    float top_p;
    std::vector<std::string> stop_sequences;
    bool stream;                      // Stream response tokens
};

/**
 * @brief AI inference response
 */
struct AIResponse {
    std::string text;
    size_t tokens_generated;
    double inference_time_ms;
    bool success;
    std::string error_message;
};

/**
 * @brief Streaming callback for AI responses
 */
using StreamCallback = std::function<void(const std::string& token)>;

/**
 * @brief AI model interface
 */
class IAIModel {
public:
    virtual ~IAIModel() = default;

    /**
     * @brief Initialize the model
     */
    virtual bool initialize(const AIModelConfig& config) = 0;

    /**
     * @brief Shutdown the model
     */
    virtual void shutdown() = 0;

    /**
     * @brief Perform inference
     */
    virtual AIResponse infer(const AIRequest& request) = 0;

    /**
     * @brief Perform streaming inference
     */
    virtual bool infer_stream(const AIRequest& request, StreamCallback callback) = 0;

    /**
     * @brief Get model information
     */
    virtual std::string get_model_name() const = 0;
    virtual AIModelType get_model_type() const = 0;
    virtual bool is_ready() const = 0;
};

/**
 * @brief LLaMA model implementation
 */
class LLaMAModel : public IAIModel {
public:
    LLaMAModel();
    ~LLaMAModel() override;

    bool initialize(const AIModelConfig& config) override;
    void shutdown() override;
    AIResponse infer(const AIRequest& request) override;
    bool infer_stream(const AIRequest& request, StreamCallback callback) override;

    std::string get_model_name() const override { return config_.name; }
    AIModelType get_model_type() const override { return AIModelType::LLAMA; }
    bool is_ready() const override { return initialized_; }

private:
    AIModelConfig config_;
    void* llama_ctx_;                 // llama.cpp context
    bool initialized_;
};

/**
 * @brief GPT model implementation (via API)
 */
class GPTModel : public IAIModel {
public:
    GPTModel();
    ~GPTModel() override;

    bool initialize(const AIModelConfig& config) override;
    void shutdown() override;
    AIResponse infer(const AIRequest& request) override;
    bool infer_stream(const AIRequest& request, StreamCallback callback) override;

    std::string get_model_name() const override { return config_.name; }
    AIModelType get_model_type() const override { return config_.type; }
    bool is_ready() const override { return initialized_; }

private:
    AIModelConfig config_;
    bool initialized_;

    // HTTP client for API calls
    std::string make_api_request(const std::string& endpoint, const std::string& payload);
};

/**
 * @brief AI Manager for managing multiple models
 */
class AIManager {
public:
    AIManager();
    ~AIManager();

    // Disable copy/move
    AIManager(const AIManager&) = delete;
    AIManager& operator=(const AIManager&) = delete;

    /**
     * @brief Load an AI model
     * @param config Model configuration
     * @return Model ID on success, empty string on failure
     */
    std::string load_model(const AIModelConfig& config);

    /**
     * @brief Unload a model
     * @param model_id Model ID returned by load_model()
     */
    bool unload_model(const std::string& model_id);

    /**
     * @brief Set active model
     * @param model_id Model ID to activate
     */
    bool set_active_model(const std::string& model_id);

    /**
     * @brief Get active model
     */
    std::string get_active_model() const;

    /**
     * @brief Perform inference with active model
     */
    AIResponse infer(const AIRequest& request);

    /**
     * @brief Perform streaming inference with active model
     */
    bool infer_stream(const AIRequest& request, StreamCallback callback);

    /**
     * @brief Get list of loaded models
     */
    std::vector<std::string> get_loaded_models() const;

    /**
     * @brief Get model configuration
     */
    AIModelConfig get_model_config(const std::string& model_id) const;

    /**
     * @brief Check if model is ready
     */
    bool is_model_ready(const std::string& model_id) const;

    /**
     * @brief Intelligent suggestions based on context
     * @param context Current system context
     * @return List of suggested actions
     */
    std::vector<std::string> get_suggestions(const std::string& context);

    /**
     * @brief Analyze user intent
     * @param input User input
     * @return Interpreted intent and parameters
     */
    struct Intent {
        std::string action;
        std::unordered_map<std::string, std::string> parameters;
        float confidence;
    };

    Intent analyze_intent(const std::string& input);

private:
    // Create model instance based on type
    std::unique_ptr<IAIModel> create_model(AIModelType type);

    // Generate unique model ID
    std::string generate_model_id(const std::string& name);

    // Loaded models
    std::unordered_map<std::string, std::unique_ptr<IAIModel>> models_;
    mutable std::mutex models_mutex_;

    // Active model
    std::string active_model_id_;

    // Model ID counter
    std::atomic<uint64_t> next_id_{1};
};

/**
 * @brief AI-powered features
 */
class AIFeatures {
public:
    explicit AIFeatures(AIManager* ai_manager);

    /**
     * @brief Get intelligent window arrangement suggestion
     * @param windows Current window list
     * @return Suggested arrangement
     */
    std::string suggest_window_arrangement(const std::vector<std::string>& windows);

    /**
     * @brief Generate macro from natural language description
     * @param description Natural language description
     * @return Generated macro steps
     */
    std::vector<std::string> generate_macro(const std::string& description);

    /**
     * @brief Predict next user action
     * @param context Current context
     * @return Predicted action
     */
    std::string predict_next_action(const std::string& context);

    /**
     * @brief Auto-complete command
     * @param partial_command Partial command
     * @return Suggested completions
     */
    std::vector<std::string> autocomplete_command(const std::string& partial_command);

private:
    AIManager* ai_manager_;
};

} // namespace ai
} // namespace copilot

#endif // COPILOT_AI_MANAGER_HPP
