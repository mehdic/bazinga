// Gantt Chart Visualization
class GanttChart {
    constructor() {
        this.container = document.getElementById('gantt-container');
        this.data = [];
    }

    async loadGantt() {
        try {
            const response = await fetch('/api/timeline');
            const result = await response.json();
            this.data = result.timeline || [];
            this.render();
        } catch (error) {
            console.error('Failed to load gantt data:', error);
        }
    }

    render() {
        if (!this.data || this.data.length === 0) {
            this.container.innerHTML = '<div class="placeholder"><p>No gantt data available yet...</p></div>';
            return;
        }

        // Clear container
        this.container.innerHTML = '';

        // Group by agent for parallel execution view
        const agents = [...new Set(this.data.map(d => d.agent))];

        // Set up dimensions
        const margin = { top: 40, right: 30, bottom: 60, left: 120 };
        const width = this.container.clientWidth - margin.left - margin.right;
        const height = Math.max(400, agents.length * 60);

        // Create SVG
        const svg = d3.select(this.container)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Parse timestamps and group by agent
        const timeData = this.data.map(d => ({
            ...d,
            start: new Date(d.timestamp),
            end: new Date(d.timestamp + (d.duration || 0) * 1000)
        }));

        // Create scales
        const xScale = d3.scaleTime()
            .domain([
                d3.min(timeData, d => d.start),
                d3.max(timeData, d => d.end)
            ])
            .range([0, width]);

        const yScale = d3.scaleBand()
            .domain(agents)
            .range([0, height])
            .padding(0.3);

        // X axis
        const xAxis = d3.axisBottom(xScale);
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(xAxis);

        // Y axis (agents)
        const yAxis = d3.axisLeft(yScale);
        svg.append('g')
            .call(yAxis);

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisBottom(xScale)
                .tickSize(height)
                .tickFormat('')
            )
            .style('stroke', '#333')
            .style('stroke-opacity', 0.2);

        // Gantt bars
        svg.selectAll('.gantt-bar')
            .data(timeData)
            .enter()
            .append('rect')
            .attr('class', d => `gantt-bar status-${d.status}`)
            .attr('x', d => xScale(d.start))
            .attr('y', d => yScale(d.agent) + yScale.bandwidth() * 0.2)
            .attr('width', d => Math.max(5, xScale(d.end) - xScale(d.start)))
            .attr('height', yScale.bandwidth() * 0.6)
            .attr('fill', d => this.getStatusColor(d.status))
            .attr('stroke', '#000')
            .attr('stroke-width', 1)
            .attr('opacity', 0.8)
            .append('title')
            .text(d => `${d.agent}\n${d.action}\nDuration: ${d.duration}s`);

        // Task labels
        svg.selectAll('.gantt-label')
            .data(timeData)
            .enter()
            .append('text')
            .attr('class', 'gantt-label')
            .attr('x', d => xScale(d.start) + 5)
            .attr('y', d => yScale(d.agent) + yScale.bandwidth() / 2)
            .attr('dominant-baseline', 'middle')
            .text(d => d.action.substring(0, 30) + (d.action.length > 30 ? '...' : ''))
            .style('font-size', '10px')
            .style('fill', '#ffffff')
            .style('pointer-events', 'none');
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
window.ganttChart = new GanttChart();
