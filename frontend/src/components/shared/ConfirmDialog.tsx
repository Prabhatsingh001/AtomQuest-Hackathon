import { useState } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
  requireInput?: boolean;
  inputPlaceholder?: string;
  onInputChange?: (value: string) => void;
}

export function ConfirmDialog({
  open, title, message, confirmText = 'Confirm', cancelText = 'Cancel',
  variant = 'default', onConfirm, onCancel, requireInput, inputPlaceholder, onInputChange
}: ConfirmDialogProps) {
  const [inputValue, setInputValue] = useState('');
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/25 backdrop-blur-[1px]" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-xl border border-zinc-200 p-6 max-w-md w-full">
        <h3 className="text-base font-semibold text-zinc-900 mb-1">{title}</h3>
        <p className="text-sm text-zinc-500 leading-relaxed mb-5">{message}</p>

        {requireInput && (
          <textarea
            className="w-full px-3 py-2.5 border border-zinc-200 rounded-lg text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-400 transition-all mb-5 resize-none"
            placeholder={inputPlaceholder}
            rows={3}
            value={inputValue}
            onChange={(e) => { setInputValue(e.target.value); onInputChange?.(e.target.value); }}
          />
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-zinc-700 bg-white border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={requireInput && !inputValue.trim()}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-40 ${
              variant === 'danger'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-zinc-900 text-white hover:bg-zinc-800'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
