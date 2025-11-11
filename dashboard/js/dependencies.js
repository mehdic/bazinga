// Task Dependency Graph Visualization
class DependencyGraph {
    constructor() {
        this.container = document.getElementById('dependency-container');
        this.data = null;
    }

    async loadDependencies(data) {
        if (!data || !data.group_status) {
            this.container.innerHTML = '<div class="placeholder"><p>No dependency data available yet...</p></div>';
            return;
        }

        this.data = data;
        this.renderMermaid();
    }

    renderMermaid() {
        const groups = this.data.group_status.task_groups || [];

        if (groups.length === 0) {
            this.container.innerHTML = '<div class="placeholder"><p>No task groups available yet...</p></div>';
            return;
        }

        // Generate Mermaid diagram
        let mermaidCode = 'graph TD\n';

        // Add nodes
        groups.forEach((group, idx) => {
            const groupId = `G${idx}`;
            const status = this.getGroupStatus(group);
            const color = this.getStatusColor(status);

            mermaidCode += `    ${groupId}["${group.group_name}"]:::${status}\n`;

            // Add dependencies
            if (group.dependencies && group.dependencies.length > 0) {
                group.dependencies.forEach(dep => {
                    const depIdx = groups.findIndex(g => g.group_name === dep);
                    if (depIdx !== -1) {
                        mermaidCode += `    G${depIdx} --> ${groupId}\n`;
                    }
                });
            }
        });

        // Add styling
        mermaidCode += `
    classDef completed fill:#10b981,stroke:#059669,color:#fff
    classDef in-progress fill:#f59e0b,stroke:#d97706,color:#fff
    classDef pending fill:#6b7280,stroke:#4b5563,color:#fff
    classDef failed fill:#ef4444,stroke:#dc2626,color:#fff
        `;

        // Render with Mermaid
        this.container.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;

        try {
            mermaid.init(undefined, this.container.querySelector('.mermaid'));
        } catch (error) {
            console.error('Mermaid rendering failed:', error);
            this.container.innerHTML = `<div class="error">Failed to render dependency graph</div>`;
        }
    }

    getGroupStatus(group) {
        if (group.tl_agent?.status === 'completed') return 'completed';
        if (group.dev_agent?.status === 'in-progress' ||
            group.qa_agent?.status === 'in-progress' ||
            group.tl_agent?.status === 'in-progress') {
            return 'in-progress';
        }
        if (group.dev_agent?.status === 'failed' ||
            group.qa_agent?.status === 'failed' ||
            group.tl_agent?.status === 'failed') {
            return 'failed';
        }
        return 'pending';
    }

    getStatusColor(status) {
        const colors = {
            'completed': '#10b981',
            'in-progress': '#f59e0b',
            'pending': '#6b7280',
            'failed': '#ef4444'
        };
        return colors[status] || '#6b7280';
    }
}

// Initialize
window.dependencyGraph = new DependencyGraph();
