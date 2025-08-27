import datetime
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import heapq

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Status(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

@dataclass
class Ticket:
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_date: datetime.datetime
    resolved_date: Optional[datetime.datetime] = None
    parent_ticket_id: Optional[int] = None
    assigned_to: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.created_date, str):
            self.created_date = datetime.datetime.fromisoformat(self.created_date)
        if isinstance(self.resolved_date, str) and self.resolved_date:
            self.resolved_date = datetime.datetime.fromisoformat(self.resolved_date)

# Week 4: Linked List Implementation for Ticket History
class TicketNode:
    def __init__(self, ticket: Ticket, action: str):
        self.ticket = ticket
        self.action = action  # "created", "updated", "resolved", etc.
        self.timestamp = datetime.datetime.now()
        self.next = None

class TicketHistory:
    def __init__(self):
        self.head = None
        self.size = 0
    
    def add_entry(self, ticket: Ticket, action: str):
        new_node = TicketNode(ticket, action)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
    
    def get_history(self) -> List[Dict]:
        history = []
        current = self.head
        while current:
            history.append({
                'ticket_id': current.ticket.id,
                'action': current.action,
                'timestamp': current.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'ticket_title': current.ticket.title
            })
            current = current.next
        return history

# Week 5: Queue Implementation for Standard Priority Tickets
class TicketQueue:
    def __init__(self):
        self.queue = []
    
    def enqueue(self, ticket: Ticket):
        self.queue.append(ticket)
    
    def dequeue(self) -> Optional[Ticket]:
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def size(self) -> int:
        return len(self.queue)
    
    def peek(self) -> Optional[Ticket]:
        return self.queue[0] if self.queue else None

# Week 5: Priority Queue Implementation for High Priority Tickets
class PriorityTicketQueue:
    def __init__(self):
        self.heap = []
        self.entry_finder = {}
        self.counter = 0
    
    def add_ticket(self, ticket: Ticket):
        if ticket.id in self.entry_finder:
            self.remove_ticket(ticket.id)
        
        priority = -ticket.priority.value  # Negative for max heap behavior
        entry = [priority, self.counter, ticket]
        self.entry_finder[ticket.id] = entry
        heapq.heappush(self.heap, entry)
        self.counter += 1
    
    def remove_ticket(self, ticket_id: int):
        entry = self.entry_finder.pop(ticket_id, None)
        if entry:
            entry[-1] = None  
    
    def pop_ticket(self) -> Optional[Ticket]:
        while self.heap:
            priority, count, ticket = heapq.heappop(self.heap)
            if ticket is not None:
                del self.entry_finder[ticket.id]
                return ticket
        return None
    
    def is_empty(self) -> bool:
        return not any(entry[-1] is not None for entry in self.heap)

# Week 5: Stack Implementation for Undo Functionality
class ActionStack:
    def __init__(self):
        self.stack = []
    
    def push(self, action: Dict):
        self.stack.append(action)
    
    def pop(self) -> Optional[Dict]:
        return self.stack.pop() if self.stack else None
    
    def is_empty(self) -> bool:
        return len(self.stack) == 0
    
    def peek(self) -> Optional[Dict]:
        return self.stack[-1] if self.stack else None

class HelpDeskSystem:
    def __init__(self):
        self.tickets = {}
        self.next_ticket_id = 1
        self.history = TicketHistory()
        self.standard_queue = TicketQueue()
        self.priority_queue = PriorityTicketQueue()
        self.action_stack = ActionStack()
        
        # Load sample data
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load some sample tickets for demonstration"""
        sample_tickets = [
            {
                "title": "Login issues with email authentication",
                "description": "Users cannot log in using email authentication",
                "priority": Priority.HIGH,
                "status": Status.OPEN,
                "assigned_to": "John Doe"
            },
            {
                "title": "Database connection timeout",
                "description": "Application experiencing database timeouts",
                "priority": Priority.CRITICAL,
                "status": Status.IN_PROGRESS,
                "assigned_to": "Jane Smith"
            },
            {
                "title": "UI button not responding",
                "description": "Submit button not working on contact form",
                "priority": Priority.MEDIUM,
                "status": Status.OPEN
            },
            {
                "title": "Email notifications not sent",
                "description": "System not sending automated email notifications",
                "priority": Priority.LOW,
                "status": Status.RESOLVED,
                "parent_ticket_id": 2
            },
            {
                "title": "Server maintenance required",
                "description": "Routine server maintenance and updates",
                "priority": Priority.MEDIUM,
                "status": Status.CLOSED
            }
        ]
        
        for ticket_data in sample_tickets:
            self.create_ticket(**ticket_data)
    
    def create_ticket(self, title: str, description: str, priority: Priority, 
                     status: Status = Status.OPEN, assigned_to: str = None,
                     parent_ticket_id: int = None) -> Ticket:
        """Create a new ticket"""
        ticket = Ticket(
            id=self.next_ticket_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            created_date=datetime.datetime.now(),
            assigned_to=assigned_to,
            parent_ticket_id=parent_ticket_id
        )
        
        if status == Status.RESOLVED or status == Status.CLOSED:
            ticket.resolved_date = datetime.datetime.now()
        
        self.tickets[ticket.id] = ticket
        self.next_ticket_id += 1
        
        # Add to history
        self.history.add_entry(ticket, "created")
        
        # Add to appropriate queue
        if priority == Priority.HIGH or priority == Priority.CRITICAL:
            self.priority_queue.add_ticket(ticket)
        else:
            self.standard_queue.enqueue(ticket)
        
        # Record action for undo
        self.action_stack.push({
            'action': 'create',
            'ticket_id': ticket.id,
            'data': asdict(ticket)
        })
        
        return ticket
    
    def update_ticket_status(self, ticket_id: int, new_status: Status) -> bool:
        """Update ticket status"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        old_status = ticket.status
        
        # Record action for undo
        self.action_stack.push({
            'action': 'update_status',
            'ticket_id': ticket_id,
            'old_status': old_status.value,
            'new_status': new_status.value
        })
        
        ticket.status = new_status
        if new_status in [Status.RESOLVED, Status.CLOSED]:
            ticket.resolved_date = datetime.datetime.now()
        
        # Add to history
        self.history.add_entry(ticket, f"status_changed_to_{new_status.value.lower().replace(' ', '_')}")
        
        return True
    
    # Week 2: Recursive function to check ticket dependencies
    def check_dependencies_recursive(self, ticket_id: int, visited: set = None) -> Dict[str, Any]:
        """Recursively check if ticket dependencies are resolved"""
        if visited is None:
            visited = set()
        
        if ticket_id in visited:
            return {"error": f"Circular dependency detected for ticket {ticket_id}"}
        
        if ticket_id not in self.tickets:
            return {"error": f"Ticket {ticket_id} not found"}
        
        ticket = self.tickets[ticket_id]
        visited.add(ticket_id)
        
        result = {
            "ticket_id": ticket_id,
            "title": ticket.title,
            "status": ticket.status.value,
            "can_be_closed": True,
            "dependencies": []
        }
        
        # Check if this ticket has a parent dependency
        if ticket.parent_ticket_id:
            parent_result = self.check_dependencies_recursive(ticket.parent_ticket_id, visited.copy())
            result["dependencies"].append(parent_result)
            
            # Check if parent is resolved
            parent_ticket = self.tickets.get(ticket.parent_ticket_id)
            if parent_ticket and parent_ticket.status not in [Status.RESOLVED, Status.CLOSED]:
                result["can_be_closed"] = False
        
        # Check for child dependencies
        child_tickets = [t for t in self.tickets.values() if t.parent_ticket_id == ticket_id]
        for child in child_tickets:
            child_result = self.check_dependencies_recursive(child.id, visited.copy())
            result["dependencies"].append(child_result)
            
            if not child_result.get("can_be_closed", True):
                result["can_be_closed"] = False
        
        visited.remove(ticket_id)
        return result
    
    # Week 1: Analytics Dashboard using 2D Lists/Matrices
    def generate_analytics_dashboard(self) -> Dict[str, Any]:
        """Generate analytics dashboard from ticket data"""
        tickets_list = list(self.tickets.values())
        
        # Create status matrix [Status][Priority]
        status_priority_matrix = [[0 for _ in range(4)] for _ in range(4)]
        status_names = [s.value for s in Status]
        priority_names = [p.name for p in Priority]
        
        for ticket in tickets_list:
            status_idx = list(Status).index(ticket.status)
            priority_idx = ticket.priority.value - 1
            status_priority_matrix[status_idx][priority_idx] += 1
        
      
        time_matrix = []
        today = datetime.datetime.now()
        
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            day_stats = [0, 0]  # [created, resolved]
            
            for ticket in tickets_list:
                # Count created tickets
                if ticket.created_date.date() == date.date():
                    day_stats[0] += 1
                
                # Count resolved tickets
                if (ticket.resolved_date and 
                    ticket.resolved_date.date() == date.date()):
                    day_stats[1] += 1
            
            time_matrix.append([date.strftime("%Y-%m-%d")] + day_stats)
        
        return {
            "total_tickets": len(tickets_list),
            "status_summary": {
                status.value: sum(1 for t in tickets_list if t.status == status)
                for status in Status
            },
            "priority_summary": {
                priority.name: sum(1 for t in tickets_list if t.priority == priority)
                for priority in Priority
            },
            "status_priority_matrix": {
                "headers": ["Status"] + priority_names,
                "rows": [[status_names[i]] + status_priority_matrix[i] for i in range(4)]
            },
            "time_analysis": {
                "headers": ["Date", "Created", "Resolved"],
                "data": time_matrix
            },
            "queue_status": {
                "standard_queue_size": self.standard_queue.size(),
                "priority_queue_active": not self.priority_queue.is_empty()
            }
        }
    
    def process_next_ticket(self) -> Optional[Ticket]:
        """Process next ticket from queues (priority first)"""
        # Try priority queue first
        ticket = self.priority_queue.pop_ticket()
        if ticket:
            self.action_stack.push({
                'action': 'process_from_priority_queue',
                'ticket_id': ticket.id
            })
            return ticket
        
        # Try standard queue
        ticket = self.standard_queue.dequeue()
        if ticket:
            self.action_stack.push({
                'action': 'process_from_standard_queue',
                'ticket_id': ticket.id
            })
            return ticket
        
        return None
    
    def undo_last_action(self) -> bool:
        """Undo the last action using stack"""
        if self.action_stack.is_empty():
            return False
        
        action = self.action_stack.pop()
        
        if action['action'] == 'create':
            # Remove the created ticket
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                del self.tickets[ticket_id]
                return True
        
        elif action['action'] == 'update_status':
            # Revert status change
            ticket_id = action['ticket_id']
            if ticket_id in self.tickets:
                old_status = Status(action['old_status'])
                self.tickets[ticket_id].status = old_status
                if old_status not in [Status.RESOLVED, Status.CLOSED]:
                    self.tickets[ticket_id].resolved_date = None
                return True
        
        return False
    
    def display_ticket_details(self, ticket_id: int):
        """Display detailed information about a ticket"""
        if ticket_id not in self.tickets:
            print(f"❌ Ticket {ticket_id} not found.")
            return
        
        ticket = self.tickets[ticket_id]
        print(f"\n📋 Ticket Details - ID: {ticket.id}")
        print("=" * 50)
        print(f"Title: {ticket.title}")
        print(f"Description: {ticket.description}")
        print(f"Priority: {ticket.priority.name}")
        print(f"Status: {ticket.status.value}")
        print(f"Created: {ticket.created_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if ticket.assigned_to:
            print(f"Assigned to: {ticket.assigned_to}")
        
        if ticket.parent_ticket_id:
            print(f"Parent Ticket: {ticket.parent_ticket_id}")
        
        if ticket.resolved_date:
            print(f"Resolved: {ticket.resolved_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show dependency check
        print("\n🔗 Dependency Check:")
        deps = self.check_dependencies_recursive(ticket_id)
        if "error" in deps:
            print(f"❌ {deps['error']}")
        else:
            print(f"✅ Can be closed: {deps['can_be_closed']}")
            if deps["dependencies"]:
                print("   Dependencies found - check recursively for details")

def print_matrix(title: str, headers: List[str], rows: List[List]):
    """Utility function to print matrices nicely"""
    print(f"\n {title}")
    print("=" * 60)
    
    # Print headers
    header_row = " | ".join(f"{h:>12}" for h in headers)
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(f"{str(cell):>12}" for cell in row)
        print(row_str)

def main():
    """Week 3: Main application menu and user input handling loop"""
    system = HelpDeskSystem()
    
    while True:
        print("\n" + "="*60)
        print("🎫 INTERACTIVE HELP DESK TICKET SYSTEM")
        print("="*60)
        print("1.   View Analytics Dashboard")
        print("2.   Create New Ticket")
        print("3.   View All Tickets")
        print("4.   View Ticket Details")
        print("5.   Update Ticket Status")
        print("6.   Check Dependencies (Recursive)")
        print("7.   Process Next Ticket")
        print("8.   View Ticket History")
        print("9.   Undo Last Action")
        print("10.  Queue Status")
        print("0.   Exit")
        print("-" * 60)
        
        try:
            choice = input("Enter your choice (0-10): ").strip()
            
            if choice == "0":
                print("👋 Thank you for using the Help Desk System!")
                break
            
            elif choice == "1":
                # Analytics Dashboard
                analytics = system.generate_analytics_dashboard()
                
                print(f"\n📊 ANALYTICS DASHBOARD")
                print("="*60)
                print(f"📈 Total Tickets: {analytics['total_tickets']}")
                
                print(f"\n📋 Status Summary:")
                for status, count in analytics['status_summary'].items():
                    print(f"   {status}: {count}")
                
                print(f"\n⚡ Priority Summary:")
                for priority, count in analytics['priority_summary'].items():
                    print(f"   {priority}: {count}")
                
                # Print matrices
                matrix_data = analytics['status_priority_matrix']
                print_matrix("Status vs Priority Matrix", 
                           matrix_data['headers'], matrix_data['rows'])
                
                time_data = analytics['time_analysis']
                print_matrix("Time Analysis (Last 7 Days)", 
                           time_data['headers'], time_data['data'])
            
            elif choice == "2":
                # Create New Ticket
                print(f"\n📝 CREATE NEW TICKET")
                print("-" * 30)
                
                title = input("Title: ").strip()
                if not title:
                    print("❌ Title cannot be empty.")
                    continue
                
                description = input("Description: ").strip()
                if not description:
                    print("❌ Description cannot be empty.")
                    continue
                
                print("Priority levels: 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL")
                try:
                    priority_val = int(input("Priority (1-4): ").strip())
                    if priority_val not in [1, 2, 3, 4]:
                        raise ValueError
                    priority = Priority(priority_val)
                except (ValueError, TypeError):
                    print("❌ Invalid priority. Using MEDIUM as default.")
                    priority = Priority.MEDIUM
                
                assigned_to = input("Assigned to (optional): ").strip() or None
                
                parent_id = input("Parent ticket ID (optional): ").strip()
                parent_ticket_id = None
                if parent_id:
                    try:
                        parent_ticket_id = int(parent_id)
                        if parent_ticket_id not in system.tickets:
                            print(f"⚠️  Warning: Parent ticket {parent_ticket_id} not found.")
                            parent_ticket_id = None
                    except ValueError:
                        print("❌ Invalid parent ticket ID.")
                
                ticket = system.create_ticket(title, description, priority, 
                                            assigned_to=assigned_to,
                                            parent_ticket_id=parent_ticket_id)
                print(f"✅ Ticket created successfully! ID: {ticket.id}")
            
            elif choice == "3":
                # View All Tickets
                print(f"\n📋 ALL TICKETS")
                print("="*100)
                print(f"{'ID':>3} | {'Title':<30} | {'Priority':<8} | {'Status':<12} | {'Assigned':<15} | {'Created'}")
                print("-"*100)
                
                for ticket in system.tickets.values():
                    assigned = ticket.assigned_to or "Unassigned"
                    print(f"{ticket.id:>3} | {ticket.title[:30]:<30} | {ticket.priority.name:<8} | "
                          f"{ticket.status.value:<12} | {assigned[:15]:<15} | "
                          f"{ticket.created_date.strftime('%Y-%m-%d %H:%M')}")
            
            elif choice == "4":
                # View Ticket Details
                try:
                    ticket_id = int(input("Enter ticket ID: ").strip())
                    system.display_ticket_details(ticket_id)
                except ValueError:
                    print("❌ Invalid ticket ID.")
            
            elif choice == "5":
                # Update Ticket Status
                try:
                    ticket_id = int(input("Enter ticket ID: ").strip())
                    if ticket_id not in system.tickets:
                        print("❌ Ticket not found.")
                        continue
                    
                    print("Status options:")
                    for i, status in enumerate(Status, 1):
                        print(f"{i}. {status.value}")
                    
                    status_choice = int(input("Select new status (1-4): ").strip())
                    if status_choice not in [1, 2, 3, 4]:
                        raise ValueError
                    
                    new_status = list(Status)[status_choice - 1]
                    
                    if system.update_ticket_status(ticket_id, new_status):
                        print(f"✅ Ticket {ticket_id} status updated to {new_status.value}")
                    else:
                        print("❌ Failed to update ticket status.")
                        
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
            
            elif choice == "6":
                # Check Dependencies
                try:
                    ticket_id = int(input("Enter ticket ID to check dependencies: ").strip())
                    deps = system.check_dependencies_recursive(ticket_id)
                    
                    print(f"\n🔗 DEPENDENCY CHECK FOR TICKET {ticket_id}")
                    print("="*60)
                    
                    if "error" in deps:
                        print(f"❌ {deps['error']}")
                    else:
                        print(f"📋 Ticket: {deps['title']}")
                        print(f"📊 Status: {deps['status']}")
                        print(f"✅ Can be closed: {'Yes' if deps['can_be_closed'] else 'No'}")
                        
                        if deps['dependencies']:
                            print(f"\n📎 Found {len(deps['dependencies'])} dependencies")
                            print("   (Use recursive function to explore further)")
                        else:
                            print("\n✅ No dependencies found")
                            
                except ValueError:
                    print("❌ Invalid ticket ID.")
            
            elif choice == "7":
                # Process Next Ticket
                print(f"\n⚡ PROCESSING NEXT TICKET")
                print("-" * 30)
                
                ticket = system.process_next_ticket()
                if ticket:
                    print(f"✅ Processing Ticket ID: {ticket.id}")
                    print(f"   Title: {ticket.title}")
                    print(f"   Priority: {ticket.priority.name}")
                    print(f"   Status: {ticket.status.value}")
                else:
                    print("📭 No tickets in queue to process.")
            
            elif choice == "8":
                # View Ticket History
                history = system.history.get_history()
                
                print(f"\n📚 TICKET HISTORY (Chronological)")
                print("="*80)
                
                if not history:
                    print("📭 No history available.")
                else:
                    print(f"{'Timestamp':<20} | {'Ticket ID':<10} | {'Action':<20} | {'Title'}")
                    print("-"*80)
                    
                    for entry in history[:20]:  # Show last 20 entries
                        print(f"{entry['timestamp']:<20} | {entry['ticket_id']:<10} | "
                              f"{entry['action']:<20} | {entry['ticket_title'][:30]}")
                    
                    if len(history) > 20:
                        print(f"\n... and {len(history) - 20} more entries")
            
            elif choice == "9":
                # Undo Last Action
                print(f"\n↩️  UNDO LAST ACTION")
                print("-" * 20)
                
                if system.undo_last_action():
                    print("✅ Last action undone successfully.")
                else:
                    print("❌ No actions to undo.")
            
            elif choice == "10":
                # Queue Status
                analytics = system.generate_analytics_dashboard()
                queue_info = analytics['queue_status']
                
                print(f"\n📈 QUEUE STATUS")
                print("="*40)
                print(f"📋 Standard Queue Size: {queue_info['standard_queue_size']}")
                print(f"⚡ Priority Queue Active: {'Yes' if queue_info['priority_queue_active'] else 'No'}")
                
                next_standard = system.standard_queue.peek()
                if next_standard:
                    print(f"👁️  Next Standard Ticket: {next_standard.title[:40]}")
                else:
                    print("👁️  Next Standard Ticket: None")
            
            else:
                print("❌ Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()