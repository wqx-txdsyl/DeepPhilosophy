// Existing discipline URLs now open the corresponding complete album.
import { Navigate, useParams } from 'react-router-dom';
import { getDiscipline } from '../data/moreContent';
import { moreAlbumPath } from '../data/moreExplorer';

export default function MoreDisciplinePage() {
  const { discipline } = useParams();
  return <Navigate to={getDiscipline(discipline) ? moreAlbumPath(discipline) : '/more'} replace />;
}
