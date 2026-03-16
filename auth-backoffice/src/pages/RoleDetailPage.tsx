import { useParams } from "react-router";

export default function RoleDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Role Detail</h1>
      <p className="text-gray-500">Role ID: {id}</p>
      <p className="text-gray-500">Role detail view coming soon.</p>
    </div>
  );
}
