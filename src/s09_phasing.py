from enum import Enum, auto, unique
from pyuvm import uvm_object
from s13_predefined_component_classes import *
import error_classes
import threading
import utility_classes
'''
9.1

This is a Pythonic implementation of phasing. It replaces the uvm_phase_type objects
with uvm_phase_type classes, which the phases inherit. This means we do not pass
the phase type as a call to the constructor.

This violates the notion of following the spec strictly but this is justified 
here because this part of the spec has to more to do with SystemVerilog's
limitation (no multiple inheritance) than with what the user sees.

VIP developers can use this approach more easily as well, though custom phasing
remains a relatively rare implementation pattern

'''


@unique
class PhaseType ( Enum ):
    TOPDOWN = auto ()
    BOTTOMUP = auto ()
    TASK=auto()

@unique
class PyuvmPhases ( Enum ):

    BUILD = ('build_phase', PhaseType.TOPDOWN)
    CONNECT=('connect_phase', PhaseType.BOTTOMUP)
    END_OF_ELABORATION=('end_of_elaboration_phase', PhaseType.BOTTOMUP)
    START_OF_SIMULATION=('start_of_simulation_phase', PhaseType.BOTTOMUP)
    RUN=('run_phase', PhaseType.TASK)
    EXTRACT=('extract_phase', PhaseType.BOTTOMUP)
    CHECK=('check_phase', PhaseType.BOTTOMUP)
    REPORT=('report_phase',PhaseType.BOTTOMUP)
    FINAL=('final_phase',PhaseType.TOPDOWN)

# F.2.5.2  uvm_phase_state
@unique
class uvm_phase_state(Enum):
    """ The set of possible states of a phase """
    UVM_PHASE_UNINITIALIZED = auto()
    UVM_PHASE_DORMANT = auto()
    UVM_PHASE_SCHEDULED = auto()
    UVM_PHASE_SYNCING = auto()
    UVM_PHASE_STARTED = auto()
    UVM_PHASE_EXECUTING = auto()
    UVM_PHASE_READY_TO_END = auto()
    UVM_PHASE_ENDED = auto()
    UVM_PHASE_CLEANUP = auto()
    UVM_PHASE_JUMPING = auto()
    UVM_PHASE_DONE = auto()

# F.5.2.3 uvm_wait_op
@unique
class uvm_wait_op(Enum):
    """Specifies the operand when using methods like uvm_phase::wait_for_state()"""
    UVM_EQ = auto()
    UVM_NE = auto()
    UVM_LT = auto()
    UVM_LTE = auto()
    UVM_GT = auto()
    UVM_GTE = auto()


# 9.3.1.2 Class declaration
class uvm_phase(uvm_object):
    def __init__(self, name = "uvm_phase", phase_parent = None):
        '''
        We don't have the phase_type argument becaues we capture this information
        with multiple inheritance

        :param name: name of the phase
        :param phase_parent: parent in the tree
        '''
        super().__init__(name)
        self.__parent = phase_parent
        self.__default_max_ready_to_end_iterations = 20
        self.__max_ready_to_end_iterations = None
        self.__state = uvm_phase_state.UVM_PHASE_UNINITIALIZED
        self.__run_count = 0
        self.__successors   = []
        self.__predecessors = []
    # 9.3.1.3.1
    def get_phase_type(self):
        '''
        :return: class object. Equivalent to calling type with the handle of this object
        '''
        return type(self)

    # 9.3.1.3.3.3
    def set_max_ready_to_end_iterations(self, max = None):
        """
        A raise and drop of objection while this phase is in phase_ready_to_end
        causes a new iteration of phase_ready_to_end unless we've
        reached this max.

        The default value is the value returned from get_max_ready_to_end_iterations
        and that value is 20 by default.

        :param max: maximum number of iterations of ready_to_end
        """
        if max is None:
            self.__max_ready_to_end_iterations = self.get_default_max_ready_to_end_iterations()
        else:
            assert (isinstance(max, int)), "max_ready-to_end_iterations must be an int"
            self.__max_ready_to_end_iterations = max

    # 9.3.1.3.4
    def get_max_ready_to_end_iterations(self):
        """
        20 by default.

        :return: current value of max_ready_to_end_iterations
        """
        if self.__max_ready_to_end_iterations is None:
            return self.get_default_max_ready_to_end_iterations()
        else:
            return self.__max_ready_to_end_iterations

    # 9.3.1.3.5
    def set_default_max_ready_to_end_iterations(self, max):
        """
        Sets the global default maximum number of iterations of phase_ready_to_end
        The default value is 20 if this is never called.

        :param max: int that is global default
        """
        assert(isinstance(max, int)), "default_max_ready_to_end_iterations must be an int"
        self.__default_max_ready_to_end_iterations = max

    # 9.3.1.3.6
    def get_default_max_ready_to_end_iterations(self):
        """
        Returns the default maximum number of iterations of ready_to_end
        :return: default maximum number of iterations of ready_to_end
        """
        return self.__default_max_ready_to_end_iterations

    # 9.3.1.4 State
    def get_state(self):
        """:return: The current phase state"""
        return self.__state

    #9.3.1.4.2
    def get_run_count(self):
        """:return: Numer of times a phase has been executed"""
        return self.__run_count

    #9.3.1.4.3
    def find_by_name(self, name, stay_in_scope = True):
        """
        Locates a phase node with the specified name and returns its
        handle.

        :param name: Name of node
        :param stay_in_scope: If True only searches within this phase's schedule and domain.
        :return: handle to phase node of the name
        """
        raise (error_classes.UVMNotImplemented("Need to implement add first to test"))

    # 9.3.1.4.4
    def find(self, phase = None, stay_in_scope = True):
        """
        Locates the phase node of the specified phase type and returns
        the handle. Does not use the _IMP in the spec
        :param phase: Phase type to find
        :param stay_in_scope: If true search only in schedule and domain
        :return: Phase of requested type
        """
        raise (error_classes.UVMNotImplemented("Need to implement add first to test"))
    # 9.3.1.3.4 These extensions replace the uvm_phase_type argument in the
    # uvm_phase constructor

    def exec_task(self, comp, phase):
        """
        Implements the functor/delegate functionality for a task phase type

        :param comp: the component whose run_task is getting called (probably)
        :param phase: the phase of the task
        """
        ...

    def exec_func(self, comp, phase):
        """
        Implements the functor/delegate functionality for the function phase
        type.

        :param comp: The component whose function is being called
        :param phase: The phase
        :return:
        """

class uvm_phase_imp(uvm_phase):
    ...

class uvm_phase_node(uvm_phase):
    ...

class phase_adder():
    def add(self, phase, with_phase=None, after_phase = None, before_phase = None,
            start_with_phase = None, end_with_phase = None):
        """
        Adds phase to the schedule or domain. The spec says we check that
        this is only being called from a UVM_PHASE_SCHEDULE or UVM_PHASE_DOMAIN.
        We enforce this with class hierarchy and multiple inheritance.
        :param phase:
        :param with_phase:
        :param after_phase:
        :param before_phase:
        :param start_with_phase:
        :param end_with_phase:
        :return:
        """

class uvm_phase_schedule(uvm_phase, phase_adder):
    ...

class uvm_phase_domain(uvm_phase, phase_adder):
    ...


# 9.4 uvm_domain

# 9.4.1
class uvm_domain(uvm_phase, uvm_phase_domain):
    domains = {}

    @staticmethod
    def get_domains():
        return uvm_domain.domains

    @staticmethod
    def add_uvm_phases(schedule):
        ...

    @classmethod
    def get_common_domain(cls):
        """
        Get a singleton handle to the common domain
        :return: common domain handle
        """
        if "common" in uvm_domain.domains:
            return uvm_domain.domains["common"]

        domain = uvm_domain("common")
        domain.add(uvm_build_phase())
        domain.add(uvm_connect_phase())
        domain.add(uvm_end_of_elaboration_phase())
        domain.add(uvm_start_of_simulation_phase())
        domain.add(uvm_run_phase())
        domain.add(uvm_extract_phase())
        domain.add(uvm_check_phase())
        domain.add(uvm_report_phase())
        domain.add(uvm_final_phase)

        uvm_domain.domains["common"] = domain

        return domain




# 9.6 uvm_task_phase

# 9.6.1
# Unlike the SV version we use multpile inheritance to capture "imp" functionality
# The SV uses composition where we use inheritance

class uvm_task_phase(uvm_phase, uvm_phase_imp):
    def __init__(self, name):
        super().__init__(name)

    def traverse(self, comp, phase, state):
        """
        Traverses the component tree and, depending upon the state, calls
        comp.phase_started(phase), execute(comp, phase), comp.phase_ready_to_end(phase),
        or comp.phase_ended(phase)

        :param comp:  The component being traversed
        :param phase: The phase used as an argument
        :param state: The state that controls behavior
        """
        assert (isinstance(comp, uvm_component)), "comp must be a uvm_component"
        assert (isinstance(phase, uvm_phase)), "phase must be a uvm_phase"
        assert (isinstance((state, uvm_phase_state))), "state must be a uvm_phase_state"

        # no m_ as in the SV because not really a protected member class
        phase.num_procs_not_yet_returned = 0
        self.__traverse(comp, phase, state)

    def __traverse(self, comp, phase, state):
        """
        Implements the traversal of the comp tree
        :param comp: the component to traverse
        :param phase: The phase we're traversing
        :param state: The state of the traversal
        """

        phase_domain = phase.get_domain()
        comp_domain  = comp.get_domain()

        for child in comp.get_children():
            self.__traverse(child, phase, state)

        if phase_domain == uvm_domain.common_domain or phase_domain == comp_domain:
            if state == uvm_phase_state.UVM_PHASE_STARTED:
                comp.current_phase = phase
                # comp.apply_verbosity_settings(phase)
                comp.phase_started(phase)
                try:
                    comp.start_phase_sequence(phase)
                except AttributeError:
                    pass
            elif state == uvm_phase_state.UVM_PHASE_EXECUTING:
                ph = self
                if self in comp.phase_imps:
                    try:
                        ph = comp.phase_imps[self]
                        ph.execute()
                    except KeyError:
                        pass
            elif state == uvm_phase_state.UVM_PHASE_READY_TO_END:
                comp.phase_ready_to_end(phase)
            elif state == uvm_phase_state.UVM_PHASE_ENDED:
                try:
                    comp.stop_phase_sequence(phase)
                except AttributeError:
                    pass
                comp.phase_ended(phase)
                comp.current_phase = None
            else:
                raise error_classes.UVMBadPhase(f"Bad phase state {state}")

    def fork_code(self, comp, phase):
        phase.num_procs_not_yet_returned += 1
        self.exec_task(comp, phase)
        phase.num_procs_not_yet_returned -= 1

    def execute(self, comp, phase):
        assert (isinstance(comp, uvm_component)), "comp must be a uvm_component"
        assert (isinstance(phase, uvm_phase)), "phase must be a uvm_phase"
        fork = threading.Thread(target = self.fork_code, args = (comp, phase) )
        fork.start()

# This version of the uvm_topdown_phase ignores
# the states as these are there to handle
# simulation delta cycles.  We don't have simulation
# delta cycles.
#
# This is a partial implementation. It traverses from
# the top down calling the correct common phase task.
# There are no provisions for other tasks.
class uvm_topdown_phase(uvm_phase, uvm_phase_imp):
    """
    Runs phases from the top down.
    """

    def traverse(self, comp, phase, state):








# 9.8 Predefined Phases
# 9.8.1 Common Phases
# These are all Singleton objects
class common_phase(metaclass=utility_classes.Singleton, uvm_topdown_phase):
    """
    A uvm_topdown_phase that is also a singleton. Used for common phases
    """
    ...

# The common phases are described in the order of their execution.
# 9.8.1.1
class uvm_build_phase(common_phase):
    ...

# 9.8.1.2
class uvm_connect_phase(common_phase):
    ...

# 9.8.1.3
class uvm_end_of_elaboration_phase(common_phase):
    ...

# 9.8.1.4
class uvm_start_of_simulation_phase(common_phase):
    ...

# 9.8.1.5
class uvm_run_phase(metaclass=utility_classes.Singleton, uvm_task_phase):
    ...

# 9.8.1.6
class uvm_extract_phase(common_phase):
    ...

# 9.8.1.7
class uvm_check_phase(common_phase):
    ...

# 9.8.1.8
class uvm_report_phase(common_phase):
    ...

# 9.8.1.9
class uvm_final_phase(common_phase):
    ...
# 9.8.2
# Left as an exercise for an enterprising soul


