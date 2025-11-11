/**
 * Quality Metrics Module
 * Displays quality dashboard metrics when available
 */

const QualityMetrics = (function() {

    /**
     * Render quality metrics
     */
    function render(data) {
        const section = document.getElementById('quality-section');
        const container = document.getElementById('quality-container');

        if (!data.quality_dashboard) {
            // Hide section if no quality data
            section.style.display = 'none';
            return;
        }

        // Show section
        section.style.display = 'block';

        const quality = data.quality_dashboard;

        // Update overall score circle
        updateScoreCircle(quality.overall_health_score || 0);

        // Update individual metrics
        updateMetricCard('security', quality.metrics?.security);
        updateMetricCard('coverage', quality.metrics?.coverage);
        updateMetricCard('lint', quality.metrics?.lint);
        updateMetricCard('velocity', quality.metrics?.velocity);

        // Show anomalies and recommendations if present
        if (quality.anomalies && quality.anomalies.length > 0) {
            showAnomalies(quality.anomalies);
        }

        if (quality.recommendations && quality.recommendations.length > 0) {
            showRecommendations(quality.recommendations);
        }
    }

    /**
     * Update score circle
     */
    function updateScoreCircle(score) {
        const circle = document.getElementById('overall-score-circle');
        const valueEl = document.getElementById('overall-score');

        if (!circle || !valueEl) return;

        valueEl.textContent = Math.round(score);

        // Update circle color based on score
        const percentage = score;
        let color = '#6e7681'; // gray

        if (score >= 80) {
            color = '#3fb950'; // green
        } else if (score >= 60) {
            color = '#d29922'; // yellow
        } else if (score >= 40) {
            color = '#d29922'; // yellow
        } else {
            color = '#f85149'; // red
        }

        // Update conic gradient
        circle.style.background = `conic-gradient(${color} ${percentage}%, var(--bg-tertiary) ${percentage}%)`;
    }

    /**
     * Update metric card
     */
    function updateMetricCard(metricType, metricData) {
        const card = document.getElementById(`${metricType}-metric`);
        if (!card) return;

        if (!metricData) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';

        const valueEl = card.querySelector('.metric-value');
        const trendEl = card.querySelector('.metric-trend');

        if (valueEl) {
            valueEl.textContent = Math.round(metricData.score || 0);

            // Color based on score
            if (metricData.score >= 80) {
                valueEl.style.color = '#3fb950';
            } else if (metricData.score >= 60) {
                valueEl.style.color = '#d29922';
            } else {
                valueEl.style.color = '#f85149';
            }
        }

        if (trendEl && metricData.trend) {
            const trendIcon = getTrendIcon(metricData.trend);
            trendEl.textContent = `${trendIcon} ${capitalize(metricData.trend)}`;
            trendEl.className = `metric-trend ${metricData.trend}`;
        }
    }

    /**
     * Get trend icon
     */
    function getTrendIcon(trend) {
        switch (trend) {
            case 'improving':
                return '📈';
            case 'stable':
                return '➡️';
            case 'declining':
                return '📉';
            default:
                return '';
        }
    }

    /**
     * Capitalize string
     */
    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Show anomalies
     */
    function showAnomalies(anomalies) {
        // TODO: Add anomalies section to UI if needed
        console.log('Quality anomalies:', anomalies);
    }

    /**
     * Show recommendations
     */
    function showRecommendations(recommendations) {
        // TODO: Add recommendations section to UI if needed
        console.log('Quality recommendations:', recommendations);
    }

    /**
     * Update quality metrics (called when data changes)
     */
    function update(data) {
        render(data);
    }

    return {
        render,
        update
    };
})();
