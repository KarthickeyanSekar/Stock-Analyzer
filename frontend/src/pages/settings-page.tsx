import { JournalSettingsForm } from '@/features/trade-journal';

export function SettingsPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Defaults for new journal plans. Plans already started keep the values they were started
          with.
        </p>
      </div>
      <JournalSettingsForm />
    </div>
  );
}
