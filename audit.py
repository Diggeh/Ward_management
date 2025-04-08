import logging
import os
import json
from datetime import datetime
from flask import current_app, g
from flask_login import current_user

class AuditLogger:
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        
        
        log_dir = os.path.join(app.root_path, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        
        if not self.logger.handlers:
            
            handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'))
            
            
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            
            
            self.logger.addHandler(handler)
        
        
        app.log_audit = self.log_audit
        
        
        app.jinja_env.globals.update(log_audit=self.log_audit)
    
    def log_audit(self, entity_type, entity_id, action, details=None):
        if details is None:
            details = {}
        
        
        user_id = 'Anonymous'
        username = 'Unknown'
        if current_user.is_authenticated:
            user_id = current_user.id
            username = current_user.username
        
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'username': username,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'action': action,
            'details': details
        }
        
        
        self.logger.info(json.dumps(log_entry))
        
        return True
    
    def get_logs(self, entity_type=None, date_from=None, date_to=None, user_id=None, limit=100):
        logs = []
        
        
        log_file = os.path.join(self.app.root_path, 'logs', 'audit.log')
        
        if not os.path.exists(log_file):
            return logs
        
        
        from_date = None
        to_date = None
        
        if date_from:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            
        if date_to:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
        
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    
                    entry = json.loads(line.strip())
                    
                    
                    if entity_type and entry.get('entity_type') != entity_type:
                        continue
                        
                    if from_date:
                        log_date = datetime.strptime(entry.get('timestamp')[:19], '%Y-%m-%d %H:%M:%S')
                        if log_date < from_date:
                            continue
                            
                    if to_date:
                        log_date = datetime.strptime(entry.get('timestamp')[:19], '%Y-%m-%d %H:%M:%S')
                        if log_date > to_date:
                            continue
                            
                    if user_id and str(entry.get('user_id')) != str(user_id):
                        continue
                    
                    
                    details = entry.get('details', {})
                    
                    
                    changes = []
                    if 'changes' in details:
                        for field, values in details['changes'].items():
                            changes.append({
                                'field': field,
                                'old_value': values.get('old', ''),
                                'new_value': values.get('new', '')
                            })
                    
                    
                    entity_name = (
                        details.get('patient_name', '') or 
                        details.get('ward_name', '') or 
                        details.get('bed_name', '') or
                        details.get('user_name', '') or
                        f"ID: {entry.get('entity_id', '')}"
                    )
                    
                    logs.append({
                        'id': len(logs) + 1,  
                        'timestamp': entry.get('timestamp'),
                        'user': entry.get('username'),
                        'entity_type': entry.get('entity_type'),
                        'entity_name': entity_name,
                        'operation': entry.get('action'),
                        'changes': changes
                    })
                except Exception as e:
                    
                    continue
        
        
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        
        return logs[:limit]


audit_logger = AuditLogger()
