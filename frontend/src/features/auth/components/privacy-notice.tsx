import { ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

/** What personal data is stored, why, and how to delete it (DPDP Act 2023). */
export function PrivacyNotice() {
  return (
    <article className="mx-auto flex max-w-2xl flex-col gap-4 p-4 text-sm leading-relaxed md:p-6">
      <h1 className="flex items-center gap-2 text-2xl font-semibold">
        <ShieldCheck className="size-6 text-primary" aria-hidden="true" /> Privacy notice
      </h1>
      <p>
        Stock Analyzer is a private, invite-only tool for learning and research. It does not place
        trades and gives no investment advice.
      </p>
      <h2 className="text-base font-semibold">What we store</h2>
      <ul className="list-disc pl-5">
        <li>
          From your sign-in provider: your email address, your name and a provider account id.
        </li>
        <li>What you create: journal plans, journal settings and your watchlist.</li>
        <li>Security records: when you sign in, and changes admins make (the audit log).</li>
      </ul>
      <h2 className="text-base font-semibold">Why</h2>
      <p>
        Only to let you sign in, keep your journal private to you, and keep the service secure. Your
        data is not sold or shared, and no advertising or tracking is used.
      </p>
      <h2 className="text-base font-semibold">Deleting your data</h2>
      <p>
        Use <span className="font-medium">Account › Delete my account</span>. Your account, plans,
        settings, watchlist and sessions are deleted immediately; the audit log keeps only that an
        account was deleted, without your details.
      </p>
      <Link to="/" className="text-primary hover:underline">
        Back to the app
      </Link>
    </article>
  );
}
