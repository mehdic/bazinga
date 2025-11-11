/**
 * Workflow Visualization Module
 * Generates and renders Mermaid diagrams from coordination data
 */

const WorkflowViz = (function() {
    let currentData = null;
    let aiDiagramEnabled = false;

    /**
     * Initialize Mermaid
     */
    function init() {
        mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#58a6ff',
                primaryTextColor: '#e6edf3',
                primaryBorderColor: '#30363d',
                lineColor: '#8b949e',
                secondaryColor: '#3fb950',
                tertiaryColor: '#d29922',
                background: '#0d1117',
                mainBkg: '#161b22',
                secondBkg: '#1f2937',
                textColor: '#e6edf3',
                fontSize: '16px'
            },
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }
        });
    }

    /**
     * Generate Mermaid diagram from coordination data
     */
    function generateDiagram(data) {
        currentData = data;

        if (!data.pm_state || !data.pm_state.task_groups) {
            return null;
        }

        const pmState = data.pm_state;
        const groupStatus = data.group_status || {};
        const taskGroups = pmState.task_groups;

        let mermaidCode = 'graph TD\n';

        // PM node
        mermaidCode += '    PM[Project Manager]:::pm\n';

        // Task group nodes
        Object.entries(taskGroups).forEach(([groupId, group]) => {
            const status = group.status || 'pending';
            const statusClass = status.replace('_', '');

            // Main group node
            mermaidCode += `    ${groupId}["Group ${groupId}: ${group.name}"]:::${statusClass}\n`;

            // PM to group edge
            mermaidCode += `    PM --> ${groupId}\n`;

            // Add agent pipeline for in-progress or completed groups
            if (status !== 'pending') {
                const iterations = groupStatus[groupId]?.iterations || {};

                // Developer node
                mermaidCode += `    ${groupId}_DEV["🧑‍💻 Developer"]:::agent\n`;
                mermaidCode += `    ${groupId} --> ${groupId}_DEV\n`;

                // QA node (if ran)
                if (iterations.qa > 0 || status === 'completed') {
                    mermaidCode += `    ${groupId}_QA["🧪 QA Expert"]:::agent\n`;
                    mermaidCode += `    ${groupId}_DEV --> ${groupId}_QA\n`;

                    // Tech Lead node (if ran)
                    if (iterations.tech_lead > 0 || status === 'completed') {
                        mermaidCode += `    ${groupId}_TL["👔 Tech Lead"]:::agent\n`;
                        mermaidCode += `    ${groupId}_QA --> ${groupId}_TL\n`;

                        // Done node (if completed)
                        if (status === 'completed') {
                            mermaidCode += `    ${groupId}_DONE["✅ Completed"]:::completed\n`;
                            mermaidCode += `    ${groupId}_TL --> ${groupId}_DONE\n`;
                        }
                    }
                }
            }
        });

        // Add dependencies
        Object.entries(taskGroups).forEach(([groupId, group]) => {
            if (group.dependencies && group.dependencies.length > 0) {
                group.dependencies.forEach(depId => {
                    mermaidCode += `    ${depId} -.->|depends| ${groupId}\n`;
                });
            }
        });

        // Add class definitions
        mermaidCode += '\n';
        mermaidCode += '    classDef pm fill:#58a6ff,stroke:#1f6feb,color:#0d1117,stroke-width:2px\n';
        mermaidCode += '    classDef completed fill:#3fb950,stroke:#2ea043,color:#0d1117,stroke-width:2px\n';
        mermaidCode += '    classDef inprogress fill:#d29922,stroke:#9e6a03,color:#0d1117,stroke-width:2px\n';
        mermaidCode += '    classDef pending fill:#6e7681,stroke:#484f58,color:#e6edf3,stroke-width:2px\n';
        mermaidCode += '    classDef agent fill:#8b949e,stroke:#6e7681,color:#0d1117,stroke-width:1px\n';

        return mermaidCode;
    }

    /**
     * Render diagram
     */
    async function render(data) {
        const container = document.getElementById('workflow-diagram');
        if (!container) return;

        try {
            const mermaidCode = generateDiagram(data);

            if (!mermaidCode) {
                container.innerHTML = '<div class="placeholder"><p>Waiting for task groups to be created...</p></div>';
                return;
            }

            // Clear container
            container.innerHTML = '';

            // Create element for Mermaid
            const element = document.createElement('div');
            element.className = 'mermaid';
            element.textContent = mermaidCode;
            container.appendChild(element);

            // Render
            await mermaid.run({
                nodes: container.querySelectorAll('.mermaid')
            });

            console.log('✅ Workflow diagram rendered');

        } catch (error) {
            console.error('Error rendering workflow diagram:', error);
            container.innerHTML = `
                <div class="placeholder">
                    <p style="color: #f85149;">Error rendering diagram: ${error.message}</p>
                    <p style="font-size: 0.85rem; margin-top: 1rem;">Check console for details.</p>
                </div>
            `;
        }
    }

    /**
     * Update diagram (called when data changes)
     */
    async function update(data) {
        // Check if AI diagram feature is enabled
        if (data.skills_config && data.skills_config.dashboard_ai_diagram_enabled) {
            aiDiagramEnabled = true;
            document.getElementById('generate-ai-diagram').style.display = 'inline-block';
        } else {
            aiDiagramEnabled = false;
            document.getElementById('generate-ai-diagram').style.display = 'none';
        }

        await render(data);
    }

    /**
     * Refresh diagram
     */
    async function refresh() {
        if (currentData) {
            await render(currentData);
        }
    }

    /**
     * Generate AI diagram
     */
    async function generateAIDiagram() {
        const modal = document.getElementById('ai-diagram-modal');
        const loading = document.getElementById('ai-diagram-loading');
        const content = document.getElementById('ai-diagram-content');
        const error = document.getElementById('ai-diagram-error');
        const narrative = document.getElementById('ai-narrative');
        const insights = document.getElementById('ai-insights');
        const diagramRender = document.getElementById('ai-diagram-render');

        // Show modal
        modal.classList.add('active');
        loading.style.display = 'block';
        content.style.display = 'none';
        error.style.display = 'none';

        try {
            const result = await DataLoader.generateAIDiagram();

            // Hide loading
            loading.style.display = 'none';

            if (result.error) {
                throw new Error(result.error + (result.message ? ': ' + result.message : ''));
            }

            // Show content
            content.style.display = 'block';

            // Render narrative
            narrative.innerHTML = `<p>${result.narrative || 'No narrative provided.'}</p>`;

            // Render insights
            if (result.insights && result.insights.length > 0) {
                insights.innerHTML = '<h4>💡 Key Insights</h4><ul>' +
                    result.insights.map(insight => `<li>${insight}</li>`).join('') +
                    '</ul>';
            } else {
                insights.innerHTML = '';
            }

            // Render Mermaid diagram
            if (result.mermaid) {
                diagramRender.innerHTML = '';
                const element = document.createElement('div');
                element.className = 'mermaid';
                element.textContent = result.mermaid;
                diagramRender.appendChild(element);

                await mermaid.run({
                    nodes: diagramRender.querySelectorAll('.mermaid')
                });
            } else {
                diagramRender.innerHTML = '<p>No diagram generated.</p>';
            }

        } catch (err) {
            console.error('Error generating AI diagram:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
            error.innerHTML = `
                <h4>⚠️ Error Generating AI Diagram</h4>
                <p>${err.message}</p>
                ${err.message.includes('disabled') ?
                    '<p style="margin-top: 1rem;">To enable this feature, edit <code>coordination/skills_config.json</code> and set <code>dashboard_ai_diagram_enabled: true</code></p>' :
                    ''}
            `;
        }
    }

    /**
     * Check if AI diagram is enabled
     */
    function isAIDiagramEnabled() {
        return aiDiagramEnabled;
    }

    return {
        init,
        render,
        update,
        refresh,
        generateAIDiagram,
        isAIDiagramEnabled
    };
})();
