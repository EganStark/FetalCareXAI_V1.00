/**
 * Fetal Health Prediction App
 * Frontend JavaScript for handling user interactions and API communication
 */

class FetalHealthApp {
    constructor() {
        // Update this URL if backend is running on different host/port
        this.baseURL = 'http://127.0.0.1:5000';
        this.schema = null;
        this.currentPrediction = null;
        this.currentInputData = null;
        
        this.init();
    }

    async init() {
        try {
            await this.loadSchema();
            this.setupEventListeners();
            this.loadCachedInputs();
            this.generateForm();
        } catch (error) {
            this.showError('Failed to initialize application: ' + error.message);
        }
    }

    async loadSchema() {
        try {
            const response = await fetch(`${this.baseURL}/schema`);
            if (!response.ok) throw new Error('Failed to load schema');
            this.schema = await response.json();
        } catch (error) {
            throw new Error('Unable to connect to the prediction service');
        }
    }

    setupEventListeners() {
        // Form buttons
        document.getElementById('clearBtn').addEventListener('click', () => this.clearForm());
        document.getElementById('previewBtn').addEventListener('click', () => this.previewInput());
        document.getElementById('predictBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.makePrediction();
        });
        document.getElementById('explainBtn').addEventListener('click', () => this.generateExplanation());

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.hideModal());
        });

        // Click outside modal to close
        document.getElementById('errorModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.hideModal();
        });

        // Form input changes - save to localStorage
        document.addEventListener('input', (e) => {
            if (e.target.matches('input[type="number"]')) {
                this.saveInputToCache();
            }
        });
    }

    generateForm() {
        const formFields = document.getElementById('formFields');
        formFields.innerHTML = '';

        if (!this.schema || !this.schema.features) {
            formFields.innerHTML = '<p>Unable to load form schema</p>';
            return;
        }

        Object.entries(this.schema.features).forEach(([fieldName, fieldMeta]) => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';

            const label = document.createElement('label');
            label.setAttribute('for', fieldName);
            label.textContent = this.formatFieldName(fieldName);

            const description = document.createElement('div');
            description.className = 'field-description';
            description.textContent = fieldMeta.description || '';

            const rangeInfo = document.createElement('div');
            rangeInfo.className = 'field-range';
            rangeInfo.textContent = `Range: ${fieldMeta.min} - ${fieldMeta.max}`;

            const input = document.createElement('input');
            input.type = 'number';
            input.id = fieldName;
            input.name = fieldName;
            input.min = fieldMeta.min;
            input.max = fieldMeta.max;
            input.step = fieldMeta.type === 'float' ? 'any' : '1';
            input.required = true;
            input.placeholder = `Enter value (${fieldMeta.min} - ${fieldMeta.max})`;

            formGroup.appendChild(label);
            formGroup.appendChild(description);
            formGroup.appendChild(input);
            formGroup.appendChild(rangeInfo);

            formFields.appendChild(formGroup);
        });
    }

    formatFieldName(fieldName) {
        return fieldName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    getFormData() {
        const formData = {};
        const inputs = document.querySelectorAll('#formFields input');
        
        inputs.forEach(input => {
            const value = input.value.trim();
            if (value !== '') {
                formData[input.name] = parseFloat(value);
            }
        });

        return formData;
    }

    validateFormData(data) {
        const errors = [];
        const requiredFields = this.schema.required || Object.keys(this.schema.features);

        // Check for missing fields
        requiredFields.forEach(field => {
            if (!(field in data) || data[field] === '' || isNaN(data[field])) {
                errors.push(`${this.formatFieldName(field)} is required`);
            }
        });

        // Validate ranges
        Object.entries(data).forEach(([field, value]) => {
            if (this.schema.features[field]) {
                const meta = this.schema.features[field];
                if (value < meta.min || value > meta.max) {
                    errors.push(`${this.formatFieldName(field)} must be between ${meta.min} and ${meta.max}`);
                }
            }
        });

        return errors;
    }

    async previewInput() {
        const formData = this.getFormData();
        const validationErrors = this.validateFormData(formData);

        if (validationErrors.length > 0) {
            this.showError('Please fix the following errors:\n• ' + validationErrors.join('\n• '));
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.baseURL}/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Preview failed');
            }

            this.displayPreview(result.data);
            this.showSection('previewSection');

        } catch (error) {
            this.showError('Preview failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayPreview(data) {
        const previewContent = document.getElementById('previewContent');
        previewContent.innerHTML = '';

        Object.entries(data).forEach(([field, value]) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';

            const label = document.createElement('span');
            label.className = 'label';
            label.textContent = this.formatFieldName(field);

            const valueSpan = document.createElement('span');
            valueSpan.className = 'value';
            valueSpan.textContent = value;

            previewItem.appendChild(label);
            previewItem.appendChild(valueSpan);
            previewContent.appendChild(previewItem);
        });
    }

    async makePrediction() {
        const formData = this.getFormData();
        const validationErrors = this.validateFormData(formData);

        if (validationErrors.length > 0) {
            this.showError('Please fix the following errors:\n• ' + validationErrors.join('\n• '));
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.baseURL}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Prediction failed');
            }

            this.currentPrediction = result;
            this.currentInputData = formData;
            this.displayPrediction(result);
            this.showSection('resultsSection');

        } catch (error) {
            this.showError('Prediction failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayPrediction(result) {
        const predictionResult = document.getElementById('predictionResult');
        
        const badge = document.createElement('div');
        badge.className = `prediction-badge prediction-${result.class_label.toLowerCase()}`;
        badge.textContent = result.class_label;

        const description = document.createElement('p');
        description.textContent = this.getPredictionDescription(result.class_label);
        description.style.marginTop = '1rem';
        description.style.color = 'var(--text-secondary)';

        predictionResult.innerHTML = '';
        predictionResult.appendChild(badge);
        predictionResult.appendChild(description);
    }

    getPredictionDescription(label) {
        switch (label.toLowerCase()) {
            case 'normal':
                return 'The fetal health indicators suggest normal conditions.';
            case 'suspect':
                return 'The fetal health indicators suggest potentially concerning conditions that may require monitoring.';
            case 'pathological':
                return 'The fetal health indicators suggest abnormal conditions that may require immediate medical attention.';
            default:
                return 'Prediction completed.';
        }
    }

    async generateExplanation() {
        if (!this.currentInputData) {
            this.showError('No prediction data available for explanation');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.baseURL}/explain`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentInputData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Explanation failed');
            }

            this.displayExplanation(result);
            this.showSection('explanationSection');

        } catch (error) {
            this.showError('Explanation failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayExplanation(result) {
        const explanationContent = document.getElementById('explanationContent');
        explanationContent.innerHTML = '';

        // Summary
        const summary = document.createElement('div');
        summary.className = 'explanation-summary';
        summary.innerHTML = `
            <h3>Prediction: ${result.class_label}</h3>
            <p>The following features had the most influence on this prediction:</p>
        `;
        explanationContent.appendChild(summary);

        // Feature explanations
        if (result.explanations && result.explanations.length > 0) {
            const featuresContainer = document.createElement('div');
            featuresContainer.className = 'explanation-features';

            result.explanations.forEach(explanation => {
                const featureDiv = document.createElement('div');
                featureDiv.className = 'feature-explanation';

                const featureInfo = document.createElement('div');
                featureInfo.className = 'feature-info';

                const featureName = document.createElement('div');
                featureName.className = 'feature-name';
                featureName.textContent = this.formatFieldName(explanation.feature);

                const featureValue = document.createElement('div');
                featureValue.className = 'feature-value';
                featureValue.textContent = `Value: ${explanation.value}`;

                featureInfo.appendChild(featureName);
                featureInfo.appendChild(featureValue);

                const featureImpact = document.createElement('div');
                featureImpact.className = 'feature-impact';

                const impactBadge = document.createElement('span');
                impactBadge.className = `impact-badge impact-${explanation.impact.toLowerCase()}`;
                impactBadge.textContent = explanation.impact;

                const impactWeight = document.createElement('span');
                impactWeight.className = 'impact-weight';
                impactWeight.textContent = `${explanation.weight > 0 ? '+' : ''}${explanation.weight}`;

                featureImpact.appendChild(impactBadge);
                featureImpact.appendChild(impactWeight);

                featureDiv.appendChild(featureInfo);
                featureDiv.appendChild(featureImpact);

                featuresContainer.appendChild(featureDiv);
            });

            explanationContent.appendChild(featuresContainer);
        } else {
            const noExplanation = document.createElement('p');
            noExplanation.textContent = 'No detailed explanations available.';
            noExplanation.style.color = 'var(--text-secondary)';
            explanationContent.appendChild(noExplanation);
        }

        // HTML visualization if available
        if (result.html) {
            const htmlContainer = document.createElement('div');
            htmlContainer.className = 'lime-html-visualization';
            htmlContainer.innerHTML = result.html;
            explanationContent.appendChild(htmlContainer);
        }
    }

    clearForm() {
        document.getElementById('predictionForm').reset();
        this.hideSection('previewSection');
        this.hideSection('resultsSection');
        this.hideSection('explanationSection');
        this.currentPrediction = null;
        this.currentInputData = null;
        localStorage.removeItem('fetalHealthInputs');
    }

    showSection(sectionId) {
        document.getElementById(sectionId).classList.remove('hidden');
        document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    hideSection(sectionId) {
        document.getElementById(sectionId).classList.add('hidden');
    }

    showLoading() {
        document.getElementById('loadingOverlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('errorModal').classList.add('hidden');
    }

    saveInputToCache() {
        const formData = this.getFormData();
        try {
            localStorage.setItem('fetalHealthInputs', JSON.stringify(formData));
        } catch (error) {
            console.warn('Could not save inputs to localStorage:', error);
        }
    }

    loadCachedInputs() {
        try {
            const cached = localStorage.getItem('fetalHealthInputs');
            if (cached) {
                const data = JSON.parse(cached);
                Object.entries(data).forEach(([field, value]) => {
                    const input = document.getElementById(field);
                    if (input) {
                        input.value = value;
                    }
                });
            }
        } catch (error) {
            console.warn('Could not load cached inputs:', error);
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FetalHealthApp();
});
