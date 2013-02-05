"""Utilities to deploy"""

from boto import ec2
from boto.exception import EC2ResponseError
from nxdd.utils import pflush


class Controller(object):
    """Utility class to control the cloud nodes"""

    def __init__(self, region, keypair_name, keys_folder, ssh_user='ubuntu',
                 **ec2_params):
        self.conn = ec2.connect_to_region(region, **ec2_params)

        # issue a dummy query to check the connection
        self.conn.get_all_instances()

        if not os.path.exists(keys_folder):
            os.makedirs(keys_folder)

        self.keypair_name = keypair_name
        self.key_file = os.path.join(keys_folder, keypair_name + '.pem')

        try:
            kp = self.conn.get_key_pair(keypair_name)
        except EC2ResponseError:
            kp = None

        if os.path.exists(self.key_file):
            # check that the keypair exists in the cloud
            if kp is None:
                raise RuntimeError(
                    "Found local key file '%s' but no matching keypairs"
                    " registered under the name '%s' on EC2: delete local key"
                    " file and try again."
                    % (self.key_file, keypair_name))
        else:
            if kp is not None:
                raise RuntimeError(
                    "Existing keypair registered under name '%s' on EC2 but"
                    " could not find local key file '%s'."
                    " If local file was lost, delete keypair on in AWS"
                    " Console and and try again."
                % (keypair_name, self.key_file))

            # create the keypair in the cloud and save it locally
            pflush('Creating new keypair with name:', keypair_name)
            kp = self.conn.create_key_pair(keypair_name)
            kp.save(keys_folder)
            pflush('Saved key file:', self.key_file)

        self.ssh_user = ssh_user

    def get_connection(self):
        return self.conn

    def get_running_instance(self, instance_name):

        instances = []
        for r in self.conn.get_all_instances():
            for i in r.instances:
                if ((i.tags.get('Name') == instance_name
                     or i.tags.get('name') == instance_name)
                    and i.state == 'running'):
                    instances.append(i)

        if len(instances) == 0:
            return None

        elif len(instances) > 1:
            raise RuntimeError(
                'Found more than one running instance with name %s: %r' %
                (instance_name, instances))

        return instances[0]

    def create_instance(self, instance_name, image_id, instance_type,
                        security_groups=(), ports=(22, 80, 443)):

        if not security_groups:
            # check whether there already exist a security group named after
            # the instance name
            existing_groups = [g for g in self.conn.get_all_security_groups()
                               if g.name == instance_name]
            if not existing_groups:
                # create a security group with the instance_name and grant the
                # necessary rights for ssh and 8080
                description = ("Open port 22 for ssh, 80, 443 for web server"
                               " and 8080 for direct acces to Nuxeo.")

                pflush("Creating security group for instance '%s': %s"
                      % (instance_name, description))
                sg = self.conn.create_security_group(instance_name,
                                                     description)
                for port in ports:
                    sg.authorize('tcp', port, port, '0.0.0.0/0')
            else:
                pflush("Reusing existing security group:", instance_name)

            security_groups = [instance_name]

        reservation = self.conn.run_instances(
            image_id,
            key_name=keypair_name,
            instance_type=instance_type,
            security_groups=security_groups,
        )
        assert len(reservation.instances) == 1
        instance = reservation.instances[0]
        # wait a bit before creating the tag otherwise it might be impossible
        # to fetch the status of the instance (AWS bug?).
        sleep(0.5)
        self.conn.create_tags([instance.id], {"Name": instance_name})

        retries = 0
        delay = 10
        while instance.state != 'running' and retries < 10:
            pflush("Waiting %ds for instance '%s' to startup (state='%s')..."
                  % (delay, instance_name, instance.state))
            sleep(delay)
            instance.update()
            retries += 1
        return instance

    def check_ssh_connection(self, max_retries=6, delay=10):
        self.check_connected()
        retries = 0
        while retries < max_retries:
            pflush("Checking ssh connection on: '%s'..."
                  % self.instance.dns_name)
            if self.cmd('echo "connection check"', raise_if_fail=False) == 0:
                return
            sleep(delay)
            retries += 1
        raise RuntimeError('Failed to connect via ssh')

    def connect(self, instance_name, image_id, instance_type,
                security_groups=(), ports=(22, 80, 443)):
        """Connect the crontroller to the remote node, create it if missing"""
        instance = self.get_running_instance(instance_name)

        if instance is not None:
            pflush("Reusing running instance with name '%s' at %s" % (
                instance_name, instance.dns_name))
        else:
            pflush("No running instance with name '%s', creating a new one..."
                  % instance_name)

            instance = controller.create_instance(
                instance_name, image_id, instance_type, ports=ports)

            pflush("Started instance with name '%s' at %s" % (
                instance_name, instance.dns_name))

        self.instance = instance
        self.ssh_host = "%s@%s" % (self.ssh_user, self.instance.dns_name)
        self.check_ssh_connection()

    def check_connected(self):
        if not hasattr(self, 'ssh_host') or self.ssh_host is None:
            raise RuntimeError(
                'No instance connected: call the connect method first')

    def cmd(self, cmd, raise_if_fail=True):
        self.check_connected()
        pflush(">", cmd)
        code = os.system("ssh -o \"StrictHostKeyChecking no\"  -i %s %s '%s'" %
                  (self.key_file, self.ssh_host, cmd))
        if code != 0 and raise_if_fail:
            raise RuntimeError("Remote command %s return %d" % (cmd, code))
        return code

    def put(self, local, remote, rsync=True):
        self.check_connected()
        remote = "%s:%s" % (self.ssh_host, remote)
        pflush("> Sending '%s' to '%s'" % (local, remote))
        if rsync:
            cmd = ('rsync -Paz'
                   ' --rsh "ssh -o \'StrictHostKeyChecking no\' -i %s"'
                   ' --rsync-path "sudo rsync" %s %s' %
                   (self.key_file, local, remote))
        else:
            cmd = "scp -r -o \"StrictHostKeyChecking no\" -i %s %s %s" % (
                self.key_file, local, remote)

        code = os.system(cmd)
        if code != 0:
            raise RuntimeError("Failed to send '%s' to '%s'" % (local, remote))

    def exec_script(self, local, arguments=None, sudo=False):
        self.check_connected()
        script_name = os.path.basename(local)
        self.put(local, script_name)
        if sudo:
            self.cmd('sudo chmod +x ' + script_name)
        else:
            self.cmd('chmod +x ' + script_name)
        cmd = "./%s" % script_name
        if sudo:
            cmd = "sudo " + cmd
        if arguments is not None:
            cmd += " " + arguments
        self.cmd(cmd)

    def terminate(self, instance_name=None):
        """Terminate the running instance"""
        if instance_name is None:
            self.check_connected()
            instance = self.instance
        else:
            instance = self.get_running_instance(instance_name)
            if instance is None:
                pflush('Already terminated')
                return

        pflush("Terminating instance:", instance.dns_name)
        instance.terminate()
        if hasattr(self, 'instance')  and instance.id == self.instance.id:
            self.ssh_host = None