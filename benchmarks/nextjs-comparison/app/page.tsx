'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';

// Same initial data as PyNext
const INITIAL_ISSUES = [
  { id: 1, title: "Implement user authentication", description: "Add login/signup flow with OAuth support", status: "in_progress", priority: "high" },
  { id: 2, title: "Fix navigation bug on mobile", description: "Menu doesn't close after selecting item", status: "todo", priority: "medium" },
  { id: 3, title: "Add dark mode support", description: "Implement system-aware dark mode with toggle", status: "backlog", priority: "low" },
  { id: 4, title: "Performance optimization", description: "Reduce bundle size and improve LCP", status: "done", priority: "high" },
  { id: 5, title: "Write API documentation", description: "Document all REST endpoints with examples", status: "todo", priority: "medium" },
  { id: 6, title: "Set up CI/CD pipeline", description: "GitHub Actions for testing and deployment", status: "done", priority: "urgent" },
];

const STATUS_LABELS: Record<string, string> = {
  backlog: "Backlog",
  todo: "Todo",
  in_progress: "In Progress",
  done: "Done",
};

const PRIORITY_ICONS: Record<string, string> = {
  urgent: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🟢",
};

interface Issue {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
}

function IssueCard({ 
  issue, 
  expanded, 
  onToggleExpand, 
  onDelete 
}: { 
  issue: Issue; 
  expanded: boolean; 
  onToggleExpand: () => void;
  onDelete: () => void;
}) {
  return (
    <div style={{
      background: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '12px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>{PRIORITY_ICONS[issue.priority]}</span>
          <span style={{ fontWeight: 500 }}>{issue.title}</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{
            padding: '4px 8px',
            background: '#f3f4f6',
            borderRadius: '4px',
            fontSize: '12px',
          }}>
            {STATUS_LABELS[issue.status]}
          </span>
          <button 
            onClick={onToggleExpand}
            style={{ background: 'none', border: 'none', cursor: 'pointer' }}
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>
      
      {expanded && (
        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
          <p style={{ color: '#6b7280', marginBottom: '12px' }}>{issue.description}</p>
          <button 
            onClick={onDelete}
            style={{
              padding: '6px 12px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}

function KanbanColumn({ 
  status, 
  issues, 
  expandedIds,
  onToggleExpand,
  onDelete,
  onDrop,
}: {
  status: string;
  issues: Issue[];
  expandedIds: Set<number>;
  onToggleExpand: (id: number) => void;
  onDelete: (id: number) => void;
  onDrop: (issueId: number, newStatus: string) => void;
}) {
  return (
    <div
      style={{
        flex: 1,
        background: '#f9fafb',
        borderRadius: '8px',
        padding: '12px',
        minHeight: '400px',
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        const issueId = parseInt(e.dataTransfer.getData('issueId'));
        onDrop(issueId, status);
      }}
    >
      <h3 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
        {STATUS_LABELS[status]} ({issues.length})
      </h3>
      {issues.map((issue) => (
        <div
          key={issue.id}
          draggable
          onDragStart={(e) => e.dataTransfer.setData('issueId', issue.id.toString())}
          style={{
            background: 'white',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '8px',
            cursor: 'grab',
            border: '1px solid #e5e7eb',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>{PRIORITY_ICONS[issue.priority]} {issue.title}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function IssuesPage() {
  // Track hydration timing
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.__BENCH__ = window.__BENCH__ || {};
      window.__BENCH__.hydrationEnd = performance.now();
      window.__BENCH__.hydrationTime = 
        window.__BENCH__.hydrationEnd - (window.__BENCH__.hydrationStart || window.__BENCH__.pageStart);
    }
  }, []);

  // State management (equivalent to PyNext signals)
  const [issues, setIssues] = useState<Issue[]>(INITIAL_ISSUES);
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);
  
  // Form state
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formPriority, setFormPriority] = useState('medium');
  const [formStatus, setFormStatus] = useState('todo');

  // Derived state (equivalent to PyNext memo)
  const filteredIssues = useMemo(() => {
    if (filterStatus === 'all') return issues;
    return issues.filter(i => i.status === filterStatus);
  }, [issues, filterStatus]);

  const issuesByStatus = useMemo(() => {
    const grouped: Record<string, Issue[]> = {
      backlog: [],
      todo: [],
      in_progress: [],
      done: [],
    };
    issues.forEach(issue => {
      grouped[issue.status]?.push(issue);
    });
    return grouped;
  }, [issues]);

  // Handlers
  const toggleExpand = useCallback((id: number) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const deleteIssue = useCallback((id: number) => {
    setIssues(prev => prev.filter(i => i.id !== id));
  }, []);

  const moveIssue = useCallback((issueId: number, newStatus: string) => {
    setIssues(prev => 
      prev.map(i => i.id === issueId ? { ...i, status: newStatus } : i)
    );
  }, []);

  const addIssue = useCallback(() => {
    if (!formTitle.trim()) return;
    
    const newIssue: Issue = {
      id: Date.now(),
      title: formTitle,
      description: formDescription,
      priority: formPriority,
      status: formStatus,
    };
    
    setIssues(prev => [...prev, newIssue]);
    setFormTitle('');
    setFormDescription('');
    setShowAddForm(false);
  }, [formTitle, formDescription, formPriority, formStatus]);

  return (
    <div style={{ fontFamily: 'system-ui', padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '20px' }}>
        Issues - Linear Clone (Next.js)
      </h1>

      {/* View toggle */}
      <div style={{ marginBottom: '16px' }}>
        <button
          onClick={() => setViewMode('list')}
          style={{
            padding: '6px 12px',
            marginRight: '8px',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            background: viewMode === 'list' ? '#3b82f6' : 'transparent',
            color: viewMode === 'list' ? 'white' : 'inherit',
          }}
        >
          List
        </button>
        <button
          onClick={() => setViewMode('kanban')}
          style={{
            padding: '6px 12px',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            background: viewMode === 'kanban' ? '#3b82f6' : 'transparent',
            color: viewMode === 'kanban' ? 'white' : 'inherit',
          }}
        >
          Kanban
        </button>
      </div>

      {/* Filter tabs */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        {['all', 'backlog', 'todo', 'in_progress', 'done'].map((status) => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              background: filterStatus === status ? '#3b82f6' : '#f3f4f6',
              color: filterStatus === status ? 'white' : 'inherit',
            }}
          >
            {status === 'all' ? 'All' : STATUS_LABELS[status] || status}
          </button>
        ))}
      </div>

      {/* Add issue button */}
      <button
        onClick={() => setShowAddForm(!showAddForm)}
        style={{
          padding: '8px 16px',
          background: '#10b981',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          marginBottom: '16px',
        }}
      >
        {showAddForm ? 'Cancel' : '+ Add Issue'}
      </button>

      {/* Add form */}
      {showAddForm && (
        <div style={{
          background: '#f9fafb',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '16px',
        }}>
          <input
            type="text"
            placeholder="Title"
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              marginBottom: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
            }}
          />
          <textarea
            placeholder="Description"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              marginBottom: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
            }}
          />
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <select
              value={formPriority}
              onChange={(e) => setFormPriority(e.target.value)}
              style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            <select
              value={formStatus}
              onChange={(e) => setFormStatus(e.target.value)}
              style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
            >
              <option value="backlog">Backlog</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>
          <button
            onClick={addIssue}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Create Issue
          </button>
        </div>
      )}

      {/* List view */}
      {viewMode === 'list' && (
        <div>
          {filteredIssues.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No issues found</p>
          ) : (
            filteredIssues.map((issue) => (
              <IssueCard
                key={issue.id}
                issue={issue}
                expanded={expandedIds.has(issue.id)}
                onToggleExpand={() => toggleExpand(issue.id)}
                onDelete={() => deleteIssue(issue.id)}
              />
            ))
          )}
        </div>
      )}

      {/* Kanban view */}
      {viewMode === 'kanban' && (
        <div style={{ display: 'flex', gap: '16px' }}>
          {['backlog', 'todo', 'in_progress', 'done'].map((status) => (
            <KanbanColumn
              key={status}
              status={status}
              issues={issuesByStatus[status]}
              expandedIds={expandedIds}
              onToggleExpand={toggleExpand}
              onDelete={deleteIssue}
              onDrop={moveIssue}
            />
          ))}
        </div>
      )}

      {/* Benchmark info */}
      <div style={{ marginTop: '40px', padding: '16px', background: '#f3f4f6', borderRadius: '8px' }}>
        <h3>Benchmark Info</h3>
        <p>Open DevTools console and run: <code>window.__BENCH__</code></p>
      </div>
    </div>
  );
}

// Type declaration for window
declare global {
  interface Window {
    __BENCH__: {
      pageStart: number;
      hydrationStart?: number;
      hydrationEnd?: number;
      hydrationTime?: number;
    };
  }
}
