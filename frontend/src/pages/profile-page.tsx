import { ProfileView } from '@/features/auth';

export function ProfilePage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <ProfileView />
    </div>
  );
}
