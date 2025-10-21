from dataclasses import dataclass

@dataclass
class CatalogsDTO:
    categories: list
    departments: list
    priorities: list
    analysts: list

class TicketService:
    def __init__(self, repo):
        self.repo = repo

    def catalogs(self) -> CatalogsDTO:
        return CatalogsDTO(
            categories = self.repo.get_categories(),
            departments = self.repo.get_departments(),
            priorities = self.repo.get_priorities(),
            analysts = self.repo.get_analysts()
        )

    def create(self, *, requester_id: int, subject: str, details: str,
               category_id: int, department_id: int, priority_id: int, assignee_id: int | None):
        code = self.repo.next_ticket_code()
        created = self.repo.insert_ticket(
            code=code,
            title=subject.strip(),
            description=details.strip(),
            requester_id=requester_id,
            department_id=department_id,
            category_id=category_id,
            priority_id=priority_id,
            assignee_id=assignee_id
        )
        return created
